# Kubernetes Logging Pipeline Workshop

Практический воркшоп по организации сбора логов из кластеров Kubernetes.

## 📋 Описание проекта

Этот проект демонстрирует полный цикл сбора, обработки и визуализации логов в Kubernetes-кластере:

1. **Тестовое приложение** - генерирует структурированные JSON-логи
2. **Vector Agent** - собирает логи из всех подов кластера и отправляет их в OpenSearch и Kafka
3. **Grafana** - визуализирует логи из ClickHouse

## 🏗️ Структура проекта

```
logging-pipeline-workshop/
├── app/                          # Тестовое приложение
│   ├── app.py                   # Python-приложение, генерирующее логи
│   ├── Dockerfile               # Образ для тестового приложения
│   └── docker-compose.yml       # Docker Compose для локального тестирования
│
├── k8s/                         # Kubernetes манифесты
│   ├── app/
│   │   └── deployment.yaml      # Deployment для тестового приложения
│   │
│   ├── vector-agent/            # Компоненты Vector Agent
│   │   ├── daemonset.yaml       # DaemonSet для Vector (запускается на каждой ноде)
│   │   ├── configmap.yaml       # Конфигурация Vector (источники, трансформации, sinks)
│   │   ├── rbac.yaml            # ServiceAccount и права доступа для Vector
│   │   ├── ca.yaml              # Сертификаты Yandex Cloud
│   │   ├── secret.yaml          # Секреты для OpenSearch и Kafka (создать из example)
│   │   └── secret.yaml.example  # Пример файла секретов
│   │
│   └── grafana/                 # Компоненты Grafana
│       ├── values.yaml          # Helm values для Grafana
│       ├── service.yaml         # Service для доступа к Grafana
│       ├── secret.yaml          # Секреты для Grafana (создать из example)
│       └── secret.yaml.example  # Пример файла секретов
│
└── README.md                    # Этот файл
```

## 🔧 Основные компоненты

### 1. Тестовое приложение (`app/app.py`)

Python-приложение, которое:
- Генерирует структурированные JSON-логи в формате:
  ```json
  {
    "timestamp": "2024-01-01T12:00:00Z",
    "level": "INFO",
    "message": "User action: login",
    "user_id": 1234,
    "request_id": "req-12345678",
    "duration_ms": 150,
    "status_code": 200
  }
  ```
- Симулирует различные пользовательские действия (login, view_page, purchase, logout, search)
- Генерирует логи с разными уровнями (INFO, ERROR) и кодами ответа

### 2. Vector Agent (`k8s/vector-agent/`)

**Vector** - это высокопроизводительный сборщик логов, который:
- Запускается как **DaemonSet** на каждой ноде кластера
- Собирает логи из `/var/log/pods` и `/var/log/containers`
- Обрабатывает логи через цепочку трансформаций:
  - Фильтрация по namespace (только `default`)
  - Парсинг JSON из сообщений
  - Извлечение метаданных Kubernetes (pod_name, namespace, node, zone)
  - Нормализация структуры логов
- Отправляет обработанные логи в два места:
  - **OpenSearch** (Elasticsearch-совместимый) - для поиска и анализа
  - **Kafka** - для потоковой обработки

### 3. Grafana (`k8s/grafana/`)

**Grafana** используется для визуализации логов:
- Подключена к **ClickHouse** как источнику данных
- Использует плагин `grafana-clickhouse-datasource`
- Доступна через LoadBalancer Service

## 🚀 Как использовать

### Предварительные требования

1. Kubernetes кластер с доступом к API
2. `kubectl` настроен для работы с кластером
3. Helm (для установки Grafana)
4. Доступ к Yandex Cloud Managed Services:
   - OpenSearch (Elasticsearch)
   - Kafka
   - ClickHouse

### Шаг 1: Подготовка секретов

#### Секреты для Vector Agent

Создайте файл `k8s/vector-agent/secret.yaml` на основе примера:

```bash
cp k8s/vector-agent/secret.yaml.example k8s/vector-agent/secret.yaml
```

Отредактируйте `secret.yaml` и укажите реальные учетные данные:
- `opensearch-credentials`: username и password для OpenSearch
- `kafka-credentials`: username и password для Kafka

#### Секреты для Grafana

Создайте файл `k8s/grafana/secret.yaml` на основе примера:

```bash
cp k8s/grafana/secret.yaml.example k8s/grafana/secret.yaml
```

Отредактируйте `secret.yaml` и укажите:
- `admin-user` и `admin-password` для входа в Grafana
- `password` для подключения к ClickHouse

**Важно:** Убедитесь, что namespace в секретах соответствует namespace, где будут развернуты компоненты (по умолчанию `logging` для Vector и `monitoring` для Grafana).

### Шаг 2: Создание namespace

```bash
kubectl create namespace logging
kubectl create namespace monitoring  # если используете отдельный namespace для Grafana
```

### Шаг 3: Развертывание Vector Agent

```bash
# Применяем RBAC
kubectl apply -f k8s/vector-agent/rbac.yaml

# Применяем сертификаты
kubectl apply -f k8s/vector-agent/ca.yaml

# Применяем секреты
kubectl apply -f k8s/vector-agent/secret.yaml

# Применяем конфигурацию
kubectl apply -f k8s/vector-agent/configmap.yaml

# Развертываем DaemonSet
kubectl apply -f k8s/vector-agent/daemonset.yaml
```

Проверьте статус:

```bash
kubectl get pods -n logging -l app=vector-agent
```

### Шаг 4: Развертывание тестового приложения

Сначала соберите Docker-образ:

```bash
cd app
docker buildx build --platform linux/amd64 -t cr.yandex/crphn3qaklbq3qsb1bll/app:latest .
docker push cr.yandex/crphn3qaklbq3qsb1bll/app:latest
```

Затем разверните в кластере:

```bash
kubectl apply -f k8s/app/deployment.yaml
```

Проверьте, что приложение генерирует логи:

```bash
kubectl logs -f -l app=test-app -n default
```

### Шаг 5: Развертывание Grafana

```bash
# Применяем секреты
kubectl apply -f k8s/grafana/secret.yaml

# Применяем сертификаты (если еще не применены)
kubectl apply -f k8s/vector-agent/ca.yaml

# Устанавливаем Grafana через Helm
helm repo add grafana https://grafana.github.io/helm-charts
helm repo update
helm install grafana grafana/grafana \
  -f k8s/grafana/values.yaml \
  -n monitoring \
  --create-namespace

# Применяем Service
kubectl apply -f k8s/grafana/service.yaml
```

Получите адрес Grafana:

```bash
kubectl get svc -n monitoring grafana
```

### Шаг 6: Проверка работы

1. **Проверка Vector Agent:**
   ```bash
   # Логи Vector
   kubectl logs -n logging -l app=vector-agent --tail=50
   
   # Метрики Vector (если включен API)
   kubectl port-forward -n logging <vector-pod-name> 8686:8686
   curl http://localhost:8686/metrics
   ```

2. **Проверка логов в OpenSearch:**
   - Подключитесь к OpenSearch и выполните поиск по индексу `logs-YYYY.MM.DD`

3. **Проверка логов в Kafka:**
   - Подключитесь к Kafka и проверьте топик `logs`

4. **Проверка Grafana:**
   - Откройте веб-интерфейс Grafana
   - Войдите с учетными данными из секрета
   - Проверьте подключение к ClickHouse datasource

## 🔍 Настройка и кастомизация

### Изменение фильтров Vector

В `k8s/vector-agent/configmap.yaml` можно настроить:
- **Источники логов:** изменить `exclude_paths_glob_patterns` для исключения других namespace
- **Фильтры:** изменить условие в `filter_default_namespace` для сбора логов из других namespace
- **Трансформации:** добавить дополнительные remap-трансформации для обработки логов
- **Sinks:** настроить параметры отправки в OpenSearch и Kafka

### Изменение структуры логов приложения

В `app/app.py` можно:
- Добавить новые поля в JSON-логи
- Изменить частоту генерации логов
- Добавить новые типы событий

## 📚 Дополнительные ресурсы

- [Vector Documentation](https://vector.dev/docs/)
- [Grafana Documentation](https://grafana.com/docs/)
- [Kubernetes Logging Best Practices](https://kubernetes.io/docs/concepts/cluster-administration/logging/)
