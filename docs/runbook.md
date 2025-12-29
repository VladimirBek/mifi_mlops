# Runbook: credit-scoring (учебный)

Этот runbook описывает типовые инциденты для API скоринга и действия по устранению.

## Контакты / владельцы
- Owner: команда проекта (учебно)
- Канал: (указать в вашей организации)

## SLO / SLI (минимум)
- Доступность API `/predict`: 99% (учебно)
- Ошибки 5xx: < 1%
- P95 latency: < 300ms (CPU), < 80ms (GPU) — ориентиры

## Алерт: CreditBackendDown
**Симптом:** `up{job="credit-backend"} == 0` более 2 минут.

**Диагностика**
1. `kubectl -n credit-scoring get pods -l app=credit-backend`
2. `kubectl -n credit-scoring describe pod <pod>`
3. `kubectl -n credit-scoring logs <pod> --tail=200`

**Действия**
- Если CrashLoopBackOff: проверить переменные окружения, доступность `models/nn_model.onnx`, лимиты памяти.
- Если OOMKilled: увеличить `resources.limits.memory` или оптимизировать модель (int8 / pruning).

## Алерт: CreditHighErrorRate
**Симптом:** доля 5xx > 5% за 5 минут.

**Диагностика**
1. Посмотреть логи приложения (Loki/Promtail либо `kubectl logs`).
2. Проверить внешние зависимости (например, хранилище, DVC/артефакты).

**Действия**
- Выполнить rollback (если включён canary/blue-green).
- Временно снизить нагрузку (HPA / limit traffic) или увеличить реплики.

## Drift alert (учебно)
Если Evidently отчёт показывает drift score выше порога:
1. Убедиться, что reference dataset корректно сформирован и не устарел.
2. Триггернуть DAG переобучения в Airflow (см. `docs/stage7_retrain_airflow.md`).
3. После переобучения — прогнать quality gate (ROC-AUC) и раскатить новую версию.

