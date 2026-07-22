#!/usr/bin/env bash

set -Eeuo pipefail

PROJECT_DIR="/opt/compass-survey-bot"
ENV_FILE="${PROJECT_DIR}/.env"
HEALTH_URL="http://127.0.0.1:8000/health"
HEALTH_ATTEMPTS=30
HEALTH_DELAY=3

log() {
    printf '[%s] %s\n' "$(date '+%Y-%m-%d %H:%M:%S')" "$*"
}

update_app_image() {
    local image="$1"
    local temporary_file

    temporary_file="$(mktemp)"

    sed "s|^APP_IMAGE=.*|APP_IMAGE=${image}|" \
        "${ENV_FILE}" > "${temporary_file}"

    if ! grep -q "^APP_IMAGE=${image}$" "${temporary_file}"; then
        rm -f "${temporary_file}"
        echo "Ошибка: не удалось обновить APP_IMAGE"
        return 1
    fi

    cat "${temporary_file}" > "${ENV_FILE}"
    rm -f "${temporary_file}"
}

if [[ $# -ne 1 ]]; then
    echo "Использование: $0 <полное имя Docker-образа>"
    echo "Пример: $0 ghcr.io/user/app:commit_sha"
    exit 2
fi

NEW_IMAGE="$1"

if [[ ! "${NEW_IMAGE}" =~ ^ghcr\.io/cherninilyaigorevich-ui/compass-survey-bot:[a-f0-9]{7,64}$ ]]; then
    echo "Ошибка: передан некорректный или неподдерживаемый образ:"
    echo "${NEW_IMAGE}"
    exit 2
fi

cd "${PROJECT_DIR}"

if [[ ! -f "${ENV_FILE}" ]]; then
    echo "Ошибка: файл ${ENV_FILE} не найден"
    exit 1
fi

OLD_IMAGE="$(grep -E '^APP_IMAGE=' "${ENV_FILE}" | head -n1 | cut -d= -f2-)"

if [[ -z "${OLD_IMAGE}" ]]; then
    echo "Ошибка: APP_IMAGE не найден в ${ENV_FILE}"
    exit 1
fi

if [[ "${OLD_IMAGE}" == "${NEW_IMAGE}" ]]; then
    log "Образ уже используется: ${NEW_IMAGE}"
    exit 0
fi

log "Текущий образ: ${OLD_IMAGE}"
log "Новый образ:   ${NEW_IMAGE}"

rollback() {
    local exit_code=$?

    trap - ERR

    log "Деплой неуспешен. Выполняется откат на ${OLD_IMAGE}"

    if update_app_image "${OLD_IMAGE}"; then
        docker compose pull app || true
        docker compose up -d --remove-orphans || true
        log "Откат выполнен"
    else
        log "Ошибка: не удалось восстановить APP_IMAGE"
    fi

    exit "${exit_code}"
}

trap rollback ERR

log "Обновление APP_IMAGE"

update_app_image "${NEW_IMAGE}"

log "Загрузка нового образа"

docker compose pull app

log "Запуск новой версии"

docker compose up -d --remove-orphans

log "Ожидание готовности приложения"

for attempt in $(seq 1 "${HEALTH_ATTEMPTS}"); do
    if curl --fail --silent --show-error "${HEALTH_URL}" >/dev/null; then
        log "Health check успешно пройден"

        trap - ERR

        log "Используемый образ:"
        docker compose images app

        log "Деплой успешно завершён"
        exit 0
    fi

    log "Попытка health check ${attempt}/${HEALTH_ATTEMPTS}"
    sleep "${HEALTH_DELAY}"
done

log "Приложение не прошло health check"
false
