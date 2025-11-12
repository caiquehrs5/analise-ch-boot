# """SportMonks fetcher: requests session, retries, helpers to get fixtures/teams.
#
# Configure the API key in the environment as SPORTMONKS_API_KEY before using.
# """
import argparse
import json
import os
import time
import logging
from functools import lru_cache
from pathlib import Path
from typing import Optional, Dict, Any, List, Iterator, Tuple

import pandas as pd
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

MODULE_DIR = Path(__file__).resolve().parent


def _env_file_candidates() -> List[Path]:
	candidates: List[Path] = []
	custom = os.getenv("SPORTMONKS_ENV_FILE")
	if custom:
		candidates.append(Path(custom))
	candidates.extend([
		MODULE_DIR / ".env",
		MODULE_DIR.parent / ".env",
		Path.cwd() / ".env",
	])
	seen = []
	for candidate in candidates:
		if candidate and candidate not in seen:
			seen.append(candidate)
	return seen


def _load_api_key_from_env_file() -> Optional[str]:
	current = os.getenv("SPORTMONKS_API_KEY")
	if current:
		return current
	for candidate in _env_file_candidates():
		if not candidate.is_file():
			continue
		for line in candidate.read_text(encoding="utf-8").splitlines():
			line = line.strip()
			if not line or line.startswith("#") or "=" not in line:
				continue
			key, value = line.split("=", 1)
			if key.strip() != "SPORTMONKS_API_KEY":
				continue
			clean_value = value.strip().strip('"').strip("'")
			if clean_value:
				os.environ.setdefault("SPORTMONKS_API_KEY", clean_value)
				logger.debug("SPORTMONKS_API_KEY carregada de %s", candidate)
				return clean_value
	return None


BASE_URL = os.getenv("SPORTMONKS_BASE_URL", "https://api.sportmonks.com/v3/football")
API_KEY = _load_api_key_from_env_file()

if not API_KEY:
	logger.warning("SPORTMONKS_API_KEY não definida. Defina SPORTMONKS_API_KEY no ambiente ou arquivo .env para usar a API.")

# Session with retries/backoff
_session = requests.Session()
_retries = Retry(
	total=3,
	backoff_factor=0.5,
	status_forcelist=(429, 500, 502, 503, 504),
	allowed_methods=frozenset(["GET", "POST"]),
)
_adapter = HTTPAdapter(max_retries=_retries)
_session.mount("https://", _adapter)
_session.mount("http://", _adapter)

DEFAULT_EXPORT_INCLUDES = "participants,round,stage,venue,league,scores"
DEFAULT_DIAGNOSE_INCLUDES = "participants,league"
CSV_ENCODING = "utf-8-sig"


def _extract_pagination(payload: Dict[str, Any]) -> Dict[str, Any]:
	"""Return pagination metadata regardless of v2/v3 structure."""
	if not isinstance(payload, dict):
		return {}
	if payload.get("pagination"):
		return payload["pagination"] or {}
	meta = payload.get("meta") or {}
	return meta.get("pagination") or {}


def _next_page_value(pagination: Dict[str, Any]) -> Optional[int]:
	"""Infer next page from SportMonks pagination payload."""
	if not pagination:
		return None
	next_candidate = pagination.get("next_page") or pagination.get("next")
	if isinstance(next_candidate, int):
		return next_candidate
	if isinstance(next_candidate, str) and next_candidate.isdigit():
		return int(next_candidate)
	links = pagination.get("links")
	if isinstance(links, dict) and links.get("next"):
		current = pagination.get("current_page")
		if isinstance(current, int):
			return current + 1
	total_pages = pagination.get("total_pages") or pagination.get("last_page")
	current_page = pagination.get("current_page")
	if isinstance(total_pages, int) and isinstance(current_page, int) and current_page < total_pages:
		return current_page + 1
	if pagination.get("has_more") and isinstance(current_page, int):
		return current_page + 1
	return None


def _safe_int(value: Any) -> Optional[int]:
	if value in (None, ""):
		return None
	try:
		if isinstance(value, bool):
			return int(value)
		return int(float(value))
	except (TypeError, ValueError):
		return None


def _normalize_date(value: Optional[str]) -> Optional[str]:
	if not value:
		return None
	result = value.replace("T", " ")
	for sep in ("+", "Z"):
		if sep in result:
			result = result.split(sep)[0]
	return result.strip()[:10]


def _fixture_participants(fixture: Dict[str, Any]) -> Tuple[Optional[str], Optional[str]]:
	participants = fixture.get("participants")
	if isinstance(participants, dict):
		participants = participants.get("data") or participants.get("participants")
	home_name: Optional[str] = None
	away_name: Optional[str] = None
	if isinstance(participants, list):
		for participant in participants:
			if not isinstance(participant, dict):
				continue
			meta = participant.get("meta") or participant.get("pivot") or {}
			location = meta.get("location") or meta.get("group")
			location = str(location).lower() if location else ""
			name = participant.get("name") or participant.get("short_code")
			if location in {"home", "local"}:
				home_name = name
			elif location in {"away", "visitor", "visitante"}:
				away_name = name
			elif not home_name:
				home_name = name
			elif not away_name:
				away_name = name
	if not home_name:
		home_name = (
			fixture.get("localTeam", {}).get("data", {}).get("name")
			or fixture.get("localteam", {}).get("data", {}).get("name")
			or fixture.get("home_name")
		)
	if not away_name:
		away_name = (
			fixture.get("visitorTeam", {}).get("data", {}).get("name")
			or fixture.get("visitorteam", {}).get("data", {}).get("name")
			or fixture.get("away_name")
		)
	return home_name, away_name


def _extract_score_from_dict(payload: Dict[str, Any], keys: List[str]) -> Optional[int]:
	for key in keys:
		value = payload.get(key)
		if isinstance(value, dict):
			value = value.get("score") or value.get("data", {}).get("score")
		score = _safe_int(value)
		if score is not None:
			return score
	return None


def _fixture_scores(fixture: Dict[str, Any]) -> Tuple[Optional[int], Optional[int]]:
	source_candidates = [
		fixture.get("scores"),
		fixture.get("score"),
		fixture.get("results"),
	]
	home_score: Optional[int] = None
	away_score: Optional[int] = None
	for candidate in source_candidates:
		if isinstance(candidate, dict):
			home_score = home_score or _extract_score_from_dict(
				candidate,
				["localteam_score", "home_score", "home", "localteam"],
			)
			away_score = away_score or _extract_score_from_dict(
				candidate,
				["visitorteam_score", "away_score", "away", "visitorteam"],
			)
		elif isinstance(candidate, list):
			for entry in candidate:
				if not isinstance(entry, dict):
					continue
				score_text = entry.get("score") or entry.get("display_score")
				if not score_text or "-" not in str(score_text):
					continue
				left, right = str(score_text).split("-", 1)
				h = _safe_int(left)
				a = _safe_int(right)
				if h is not None and a is not None:
					home_score = home_score or h
					away_score = away_score or a
	if home_score is None:
		home_score = _safe_int(fixture.get("localteam_score") or fixture.get("home_score"))
	if away_score is None:
		away_score = _safe_int(fixture.get("visitorteam_score") or fixture.get("away_score"))
	return home_score, away_score


def _fixture_status(fixture: Dict[str, Any]) -> Optional[str]:
	return (
		fixture.get("status")
		or fixture.get("state", {}).get("short_name")
		or fixture.get("state", {}).get("state")
		or fixture.get("time", {}).get("status", {}).get("short")
	)


def _fixture_round(fixture: Dict[str, Any]) -> Optional[str]:
	return (
		fixture.get("round", {}).get("data", {}).get("name")
		or fixture.get("round", {}).get("name")
		or fixture.get("round_name")
	)


def _fixture_venue(fixture: Dict[str, Any]) -> Optional[str]:
	return (
		fixture.get("venue", {}).get("data", {}).get("name")
		or fixture.get("venue", {}).get("name")
		or fixture.get("venue_name")
	)


def _fixture_winner(home_score: Optional[int], away_score: Optional[int], home: Optional[str], away: Optional[str]) -> Optional[str]:
	if home_score is None or away_score is None:
		return None
	if home_score == away_score:
		return "Empate"
	return home if home_score > away_score else away


def _fixture_to_row(fixture: Dict[str, Any]) -> Optional[Dict[str, Any]]:
	home, away = _fixture_participants(fixture)
	if not home or not away:
		logger.debug("Fixture %s sem participantes identificados", fixture.get("id"))
		return None
	home_score, away_score = _fixture_scores(fixture)
	row = {
		"data": _normalize_date(
			fixture.get("starting_at")
			or fixture.get("time", {}).get("starting_at", {}).get("date_time")
			or fixture.get("time", {}).get("datetime")
		),
		"rodada": _fixture_round(fixture),
		"time_casa": home,
		"time_fora": away,
		"gols_casa": home_score,
		"gols_fora": away_score,
		"vencedor": _fixture_winner(home_score, away_score, home, away),
		"status": _fixture_status(fixture),
		"estadio": _fixture_venue(fixture),
	}
	return row


def _get(path: str, params: Optional[Dict[str, Any]] = None, timeout: int = 10) -> Dict[str, Any]:
	"""Internal GET wrapper for SportMonks API.

	Adds api_token automatically when SPORTMONKS_API_KEY is set. Handles retries,
	429 rate-limit (Retry-After) and raises for other HTTP errors.
	Returns parsed JSON as dict.
	"""
	if params is None:
		params = {}
	params = params.copy()
	if API_KEY:
		params["api_token"] = API_KEY

	url = f"{BASE_URL.rstrip('/')}/{path.lstrip('/')}"
	attempts = 0
	while True:
		attempts += 1
		try:
			resp = _session.get(url, params=params, timeout=timeout)
		except requests.RequestException as e:
			logger.warning("Requisição falhou (attempt %d): %s", attempts, e)
			if attempts >= 3:
				raise
			time.sleep(0.5 * attempts)
			continue

		if resp.status_code == 429:
			retry_after = resp.headers.get("Retry-After")
			wait = int(retry_after) if retry_after and retry_after.isdigit() else (1 * attempts)
			logger.info("Rate limited, aguardando %s segundos (attempt %d)", wait, attempts)
			time.sleep(wait)
			if attempts >= 5:
				resp.raise_for_status()
			continue

		if not resp.ok:
			msg = f"Erro API {resp.status_code}: {resp.text[:200]}"
			logger.error(msg)
			resp.raise_for_status()

		try:
			data = resp.json()
		except ValueError:
			raise RuntimeError("Resposta não é JSON válida")

		return data


def get_fixtures(
	league_id: Optional[int] = None,
	date_from: Optional[str] = None,
	date_to: Optional[str] = None,
	status: Optional[str] = None,
	per_page: int = 50,
	page: int = 1,
	includes: Optional[str] = None,
	timeout: int = 10,
) -> List[Dict[str, Any]]:
	"""Return list of fixtures."""
	fixtures, _ = get_fixtures_page(
		league_id=league_id,
		date_from=date_from,
		date_to=date_to,
		status=status,
		per_page=per_page,
		page=page,
		includes=includes,
		timeout=timeout,
	)
	return fixtures


def get_fixtures_page(
	league_id: Optional[int] = None,
	date_from: Optional[str] = None,
	date_to: Optional[str] = None,
	status: Optional[str] = None,
	per_page: int = 50,
	page: int = 1,
	includes: Optional[str] = None,
	timeout: int = 10,
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
	params: Dict[str, Any] = {"per_page": per_page, "page": page}
	if league_id:
		params["league_id"] = league_id
	if date_from:
		params["date_from"] = date_from
	if date_to:
		params["date_to"] = date_to
	if status:
		params["status"] = status
	if includes:
		params["include"] = includes

	data = _get("/fixtures", params=params, timeout=timeout)
	fixtures = data.get("data") or data.get("response") or []
	return fixtures, _extract_pagination(data)


def iter_fixtures(
	league_id: Optional[int] = None,
	date_from: Optional[str] = None,
	date_to: Optional[str] = None,
	status: Optional[str] = None,
	per_page: int = 100,
	includes: Optional[str] = None,
	max_pages: Optional[int] = None,
	timeout: int = 10,
) -> Iterator[Dict[str, Any]]:
	"""Yield fixtures across all pages respecting optional limits."""
	page = 1
	pages_fetched = 0
	while True:
		fixtures, pagination = get_fixtures_page(
			league_id=league_id,
			date_from=date_from,
			date_to=date_to,
			status=status,
			per_page=per_page,
			page=page,
			includes=includes,
			timeout=timeout,
		)
		if not fixtures:
			break
		for fixture in fixtures:
			yield fixture
		pages_fetched += 1
		if max_pages and pages_fetched >= max_pages:
			break
		next_page = _next_page_value(pagination)
		if next_page:
			page = next_page
		elif len(fixtures) == per_page:
			page += 1
		else:
			break


@lru_cache(maxsize=256)
def get_team(team_id: int, includes: Optional[str] = None) -> Dict[str, Any]:
	params = {}
	if includes:
		params["include"] = includes
	data = _get(f"/teams/{team_id}", params=params)
	return data.get("data") or data.get("response") or {}


def search_teams(name: str, per_page: int = 20) -> List[Dict[str, Any]]:
	params = {"search": name, "per_page": per_page}
	data = _get("/teams/search", params=params)
	return data.get("data") or data.get("response") or []


def export_fixtures_to_csv(
	output_path: str,
	league_id: int = 71,
	date_from: Optional[str] = None,
	date_to: Optional[str] = None,
	status: Optional[str] = "FT",
	includes: Optional[str] = DEFAULT_EXPORT_INCLUDES,
	per_page: int = 200,
	max_pages: Optional[int] = None,
) -> int:
	"""Export fixtures to CSV compatible with ia_adaptativa.py."""
	rows: List[Dict[str, Any]] = []
	for fixture in iter_fixtures(
		league_id=league_id,
		date_from=date_from,
		date_to=date_to,
		status=status,
		per_page=per_page,
		includes=includes,
		max_pages=max_pages,
	):
		row = _fixture_to_row(fixture)
		if row:
			rows.append(row)
	if not rows:
		raise RuntimeError("Nenhum fixture convertido. Ajuste filtros ou inclui 'scores'.")
	df = pd.DataFrame(rows)
	if not df.empty and "data" in df.columns:
		df.sort_values("data", inplace=True, na_position="last")
	df["fonte"] = "SportMonks"
	df["data_extracao"] = pd.Timestamp.utcnow().isoformat()
	df.to_csv(output_path, index=False, encoding=CSV_ENCODING)
	logger.info("%s linhas exportadas para %s", len(df), output_path)
	return len(df)


def diagnose_connection(
	league_id: int,
	per_page: int = 5,
	date_from: Optional[str] = None,
	date_to: Optional[str] = None,
	status: Optional[str] = None,
	includes: Optional[str] = None,
) -> List[Dict[str, Any]]:
	"""Fetch a small sample of fixtures to validate connectivity quickly."""
	logger.info(
		"Testando SportMonks (league_id=%s, per_page=%s, date_from=%s, date_to=%s, status=%s)",
		league_id,
		per_page,
		date_from,
		date_to,
		status,
	)
	fixtures = get_fixtures(
		league_id=league_id,
		per_page=per_page,
		date_from=date_from,
		date_to=date_to,
		status=status,
		includes=includes or DEFAULT_DIAGNOSE_INCLUDES,
	)
	if not fixtures:
		logger.warning("A conexão funcionou, mas nenhum fixture foi retornado para os filtros informados.")
	return fixtures


def _print_sample(fixtures: List[Dict[str, Any]], sample: int = 3) -> None:
	for idx, fixture in enumerate(fixtures[:sample], start=1):
		date = (
			fixture.get("starting_at")
			or fixture.get("time", {}).get("starting_at", {}).get("date_time")
		)
		home = (
			fixture.get("participants", [{}])
			[0]
			.get("name")
			if fixture.get("participants")
			else fixture.get("localTeam", {})
			.get("data", {})
			.get("name")
		)
		away = (
			fixture.get("participants", [{}])
			[1]
			.get("name")
			if fixture.get("participants") and len(fixture["participants"]) > 1
			else fixture.get("visitorTeam", {})
			.get("data", {})
			.get("name")
		)
		print(f"{idx}. {date} - {home} x {away}")
	if fixtures:
		print("\nPrimeiro fixture (JSON bruto):")
		print(json.dumps(fixtures[0], indent=2, ensure_ascii=False)[:2000])


def _build_parser() -> argparse.ArgumentParser:
	parser = argparse.ArgumentParser(
		description="Validador rápido da API SportMonks. Requer SPORTMONKS_API_KEY no ambiente.",
	)
	parser.add_argument(
		"--league",
		type=int,
		default=71,
		help="ID da liga para testar (71 = Série A BR em muitos planos).",
	)
	parser.add_argument(
		"--per-page",
		type=int,
		default=5,
		help="Quantidade de fixtures para retornar no diagnóstico inicial.",
	)
	parser.add_argument("--from-date", dest="date_from", help="Filtrar data inicial (YYYY-MM-DD).")
	parser.add_argument("--to-date", dest="date_to", help="Filtrar data final (YYYY-MM-DD).")
	parser.add_argument("--status", help="Filtrar status do jogo, ex: FT, NS.")
	parser.add_argument(
		"--includes",
		default=DEFAULT_EXPORT_INCLUDES,
		help="Lista de includes para adicionar relacionamentos (default: %(default)s).",
	)
	parser.add_argument(
		"--save-csv",
		help="Se informado, salva todos os fixtures filtrados neste caminho CSV.",
	)
	parser.add_argument(
		"--export-per-page",
		type=int,
		default=200,
		help="Itens por página ao exportar CSV (default: %(default)s).",
	)
	parser.add_argument(
		"--max-pages",
		type=int,
		help="Limita a quantidade de páginas carregadas ao exportar CSV.",
	)
	return parser


def main() -> None:
	parser = _build_parser()
	args = parser.parse_args()

	if not API_KEY:
		raise SystemExit("Defina SPORTMONKS_API_KEY antes de rodar o validador.")

	try:
		fixtures = diagnose_connection(
			league_id=args.league,
			per_page=args.per_page,
			date_from=args.date_from,
			date_to=args.date_to,
			status=args.status,
			includes=args.includes,
		)
	except Exception as exc:  # pragma: no cover - diagnostic helper
		raise SystemExit(f"Falha ao conversar com a API: {exc}") from exc

	if fixtures:
		print(f"✅ API respondeu com {len(fixtures)} fixtures.")
		_print_sample(fixtures)
	else:
		print("⚠️ Nenhum fixture encontrado para os filtros fornecidos.")

	if args.save_csv:
		try:
			total = export_fixtures_to_csv(
				output_path=args.save_csv,
				league_id=args.league,
				date_from=args.date_from,
				date_to=args.date_to,
				status=args.status,
				includes=args.includes,
				per_page=args.export_per_page,
				max_pages=args.max_pages,
			)
		except Exception as exc:  # pragma: no cover - export helper
			raise SystemExit(f"Falha ao exportar CSV: {exc}") from exc
		print(f"💾 CSV salvo em {args.save_csv} com {total} linhas.")


if __name__ == "__main__":  # pragma: no cover
	main()
