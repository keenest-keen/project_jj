#!/usr/bin/env bash
# Запуск Постера — интерактивный скрипт
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$SCRIPT_DIR"

# ---------- Значения по умолчанию ----------
DEFAULT_PROD_INPUT="../posts_json"
DEFAULT_TEST_INPUT="../posts_json_test"

# ---------- Хелпер ----------
ask_yes_no() {
    local prompt="$1" default="$2" answer
    if [ "$default" = "y" ]; then
        read -rp "$prompt [Y/n]: " answer
        answer="${answer:-y}"
    else
        read -rp "$prompt [y/N]: " answer
        answer="${answer:-n}"
    fi
    case "${answer,,}" in
        y|yes|д|да) return 0 ;;
        *)          return 1 ;;
    esac
}

# ---------- Опрос ----------
echo "=== Запуск Постера ==="
echo

TEST_RUN="n"
if ask_yes_no "Тестовый запуск? ($DEFAULT_TEST_INPUT вместо $DEFAULT_PROD_INPUT)" n; then
    TEST_RUN="y"
fi

if [ "$TEST_RUN" = "y" ]; then
    INPUT_DIR="$DEFAULT_TEST_INPUT"
    MODE="ТЕСТОВЫЙ"
else
    INPUT_DIR="$DEFAULT_PROD_INPUT"
    MODE="ПРОДАКШН"
fi

INPUT_ABS="$(realpath -m -- "$INPUT_DIR")"

# ---------- Проверка и подтверждение ----------
if [ ! -d "$INPUT_ABS" ]; then
    echo "Ошибка: директория не найдена: $INPUT_ABS" >&2
    exit 1
fi

echo
echo "--- Параметры запуска ---"
printf '  Режим:         %s\n' "$MODE"
printf '  Рабочая папка: %s\n' "$INPUT_ABS"
echo

# ---------- Запуск ----------
echo
echo "Запускаем Poster..."
python -m poster --json-dir "$INPUT_ABS"