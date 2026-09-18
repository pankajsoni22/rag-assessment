#!/usr/bin/env bash
# Start/stop the RAG Assessment application (frontend + backend + Chroma) as
# Docker containers. Thin wrapper over docker/docker-compose.yml so nobody has
# to remember compose flags. Run `./docker/rag.sh help` for usage.
set -euo pipefail

DOCKER_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$DOCKER_DIR")"
ENV_FILE="$ROOT_DIR/.env"
ENV_EXAMPLE="$ROOT_DIR/.env.example"
REQUIRED_KEYS=(GROQ_API_KEY GOOGLE_API_KEY)

FRONTEND_URL="http://localhost:8501"
BACKEND_URL="http://localhost:8000"

if [[ -t 1 ]]; then BOLD=$'\e[1m'; RED=$'\e[31m'; GREEN=$'\e[32m'; YELLOW=$'\e[33m'; RESET=$'\e[0m'
else BOLD=""; RED=""; GREEN=""; YELLOW=""; RESET=""; fi

info() { echo "${BOLD}==>${RESET} $*"; }
warn() { echo "${YELLOW}warning:${RESET} $*" >&2; }
die()  { echo "${RED}error:${RESET} $*" >&2; exit 1; }

compose() { docker compose -f "$DOCKER_DIR/docker-compose.yml" "$@"; }

usage() {
  cat <<USAGE
Usage: ./docker/rag.sh <command> [options]

Commands:
  up                 Build images if needed and start everything (waits until healthy)
  down               Stop and remove the containers (your uploaded data is kept)
  down --purge       Also delete the data volume, i.e. ALL uploaded documents (asks first)
  restart            down + up
  status             Show container state
  logs [service]     Follow logs (service: frontend | backend | chroma; default: all)
  help               Show this help

After 'up':  frontend $FRONTEND_URL   backend $BACKEND_URL/docs
USAGE
}

check_docker() {
  command -v docker >/dev/null 2>&1 || die "docker is not installed or not on PATH."
  docker compose version >/dev/null 2>&1 || die "the Docker Compose plugin is missing (\`docker compose version\` fails)."
  docker info >/dev/null 2>&1 || die "cannot reach the Docker daemon - is Docker running (and do you have permission to use it)?"
}

# True when KEY is present in .env with a non-empty value. Never prints values.
env_has_value() {
  grep -Eq "^[[:space:]]*$1[[:space:]]*=[[:space:]]*[^[:space:]\"']" "$ENV_FILE"
}

ensure_env() {
  if [[ ! -f "$ENV_FILE" ]]; then
    [[ -f "$ENV_EXAMPLE" ]] || die ".env is missing and so is .env.example."
    cp "$ENV_EXAMPLE" "$ENV_FILE"
    die "created $ENV_FILE from .env.example. Add your API keys (${REQUIRED_KEYS[*]}) to it, then run this again."
  fi
  local missing=()
  for key in "${REQUIRED_KEYS[@]}"; do
    env_has_value "$key" || missing+=("$key")
  done
  if ((${#missing[@]})); then
    die "these are empty in $ENV_FILE: ${missing[*]}. Fill them in, then run this again."
  fi
}

cmd_up() {
  check_docker
  ensure_env
  info "Building and starting containers (first run takes a few minutes)..."
  if ! compose up --build -d --wait; then
    warn "startup failed - last log lines:"
    compose logs --tail 30 >&2 || true
    die "the application did not become healthy. Run './docker/rag.sh logs' for details."
  fi
  echo
  echo "${GREEN}${BOLD}RAG Assessment is running.${RESET}"
  echo "  Frontend: $FRONTEND_URL"
  echo "  Backend:  $BACKEND_URL  (API docs: $BACKEND_URL/docs)"
  echo "  Stop with: ./docker/rag.sh down"
}

cmd_down() {
  check_docker
  if [[ "${1:-}" == "--purge" ]]; then
    warn "this deletes the data volume - every uploaded document and its index."
    read -r -p "Type 'yes' to continue: " answer
    [[ "$answer" == "yes" ]] || die "aborted; nothing was stopped or deleted."
    compose down --volumes
    info "Stopped and deleted all data."
  else
    [[ $# -eq 0 ]] || die "unknown option '$1' (did you mean --purge?)"
    compose down
    info "Stopped. Uploaded data is kept; './docker/rag.sh up' brings it back."
  fi
}

case "${1:-help}" in
  up)      shift; [[ $# -eq 0 ]] || die "'up' takes no options."; cmd_up ;;
  down)    shift; cmd_down "$@" ;;
  restart) check_docker; cmd_down; cmd_up ;;
  status)  check_docker; compose ps ;;
  logs)    shift; check_docker; compose logs -f --tail 100 "$@" ;;
  help|-h|--help) usage ;;
  *)       usage >&2; die "unknown command '$1'." ;;
esac
