#!/usr/bin/env bash
# Генератор блога — интерактивный запуск
set -euo pipefail

SCRIPT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"
cd "$SCRIPT_DIR"

# ---------- Значения по умолчанию ----------
DEFAULT_TEST_INPUT="../posts_json_test"
DEFAULT_PROD_INPUT="../posts_json"

DEFAULT_TEST_OUTPUT="../blog"
DEFAULT_OUTPUT_PUBL="../blog"
DEFAULT_OUTPUT_PRIV="../blog_priv"

# ---------- Хелперы ----------
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

# ---------- 1. Тестовый или продакшн ----------
echo "=== Генератор блога ==="
echo

TEST_RUN="n"
if ask_yes_no "Тестовый запуск? ($DEFAULT_TEST_INPUT вместо $DEFAULT_PROD_INPUT)" n; then
    TEST_RUN="y"
fi

# ---------- 2. Входная папка ----------
if [ "$TEST_RUN" = "y" ]; then
    read -rp "Входная папка  [${DEFAULT_TEST_INPUT}]: " INPUT_DIR
    INPUT_DIR="${INPUT_DIR:-$DEFAULT_TEST_INPUT}"
else
    INPUT_DIR="$(realpath -m -- "$DEFAULT_PROD_INPUT")"
fi

# ---------- 3. Выходные папки ----------
if [ "$TEST_RUN" = "y" ]; then
    DEFAULT_TEST_OUTPUT="${DEFAULT_TEST_OUTPUT}"
    read -rp "Выходная папка [${DEFAULT_TEST_OUTPUT}]: " OUTPUT_DIR
    OUTPUT_DIR="${OUTPUT_DIR:-$DEFAULT_TEST_OUTPUT}"
fi

# ---------- 4. Очистка ----------
CLEAN="n"
if [ "$TEST_RUN" = "y" ]; then
    ask_yes_no "Очищать выходную папку перед генерацией?" y && CLEAN="y"
else
    ask_yes_no "Очищать выходные папки перед генерацией?" y && CLEAN="y"
fi

# ---------- 5. --private (только в тестовом режиме) ----------
PRIVATE="n"
if [ "$TEST_RUN" = "y" ]; then
    ask_yes_no "Запустить с флагом --private?" n && PRIVATE="y"
fi

# ---------- 6. Абсолютные пути ----------
INPUT_ABS="$(realpath -m -- "$INPUT_DIR")"
if [ "$TEST_RUN" = "y" ]; then
    OUTPUT_ABS="$(realpath -m -- "$OUTPUT_DIR")"
else
    OUTPUT_PUBL_ABS="$(realpath -m -- "$DEFAULT_OUTPUT_PUBL")"
    OUTPUT_PRIV_ABS="$(realpath -m -- "$DEFAULT_OUTPUT_PRIV")"
fi

# ---------- 7. Сводка и подтверждение ----------
echo
echo "--- Параметры запуска ---"
if [ "$TEST_RUN" = "y" ]; then
    printf '  Режим:             ТЕСТОВЫЙ\n'
    printf '  Входная папка:     %s\n' "$INPUT_ABS"
    printf '  Выходная папка:    %s\n' "$OUTPUT_ABS"
    printf '  --private:         %s\n' "$PRIVATE"
else
    printf '  Режим:             ПРОДАКШН\n'
    printf '  Входная папка:     %s\n' "$INPUT_ABS"
    printf '  Выход (публичный): %s\n' "$OUTPUT_PUBL_ABS"
    printf '  Выход (private):   %s\n' "$OUTPUT_PRIV_ABS"
fi
printf '  Очистка выхода:    %s\n' "$CLEAN"
echo

read -rp "Продолжить? [Y/n]: " CONFIRM
CONFIRM="${CONFIRM:-y}"
case "${CONFIRM,,}" in
    y|yes|д|да) ;;
    *) echo "Отменено."; exit 0 ;;
esac

# ---------- 8. Очистка выходных папок ----------
if [ "$CLEAN" = "y" ]; then
    if [ "$TEST_RUN" = "y" ]; then
        if [ -d "$OUTPUT_ABS" ]; then
            echo "Удаляю $OUTPUT_ABS ..."
            rm -rf -- "$OUTPUT_ABS"
        fi
    else
        for d in "$OUTPUT_PUBL_ABS" "$OUTPUT_PRIV_ABS"; do
            if [ -d "$d" ]; then
                echo "Удаляю $d ..."
                rm -rf -- "$d"
            fi
        done
    fi
fi

# ---------- 9. Запуск генератора ----------
cd "$SCRIPT_DIR/generator"

run_generator() {
    local out="$1"; shift
    echo
    echo ">>> Генерация в $out ..."
    python3 main.py --json-dir "$INPUT_ABS" --output-dir "$out" -v "$@"
}

if [ "$TEST_RUN" = "y" ]; then
    if [ "$PRIVATE" = "y" ]; then
        run_generator "$OUTPUT_ABS" --private
    else
        run_generator "$OUTPUT_ABS"
    fi
else
    run_generator "$OUTPUT_PUBL_ABS"            # публичный прогон
    run_generator "$OUTPUT_PRIV_ABS" --private  # приватный прогон
fi

echo
echo "Готово."