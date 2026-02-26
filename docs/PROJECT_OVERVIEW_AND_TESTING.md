# PSU Capstone 1S26 – 프로젝트 개요 및 테스트 가이드

## 1. Kickoff 발표 (PennState_Capstone_Project_Kickoff.pptx) 요약

- **제목:** oneM2M Orchestrator for gateway deployments (Penn State Capstone)
- **구성요소:** CSE(ACME), Orchestration Application(Django 선호), Gateway Agent(Python), VPN(Wireguard), Docker, Ansible
- **아키텍처:** Cloud(IN-CSE + Orchestration App) ↔ Edge(MN-CSE + Gateway Agent on SBC)
- **개념:** IN-AE(Orchestrator)가 IN-CSE에 배포 의도를 표현하고, Edge Agent가 VPN으로 연결해 MN-CSE/AE를 Docker로 배포·관리
- **Gateway Agent:** Golden image / Ansible Pull / SSH Push 등으로 SBC에 배포, MN-CSE보다 먼저 실행, Docker·VPN 관리, 부팅 시 시작·실패 시 재시작
- **단계:** Step 0(팀·도구), Step 1(oneM2M 튜토리얼·rPI), Step 2(IN/MN-CSE Docker·Django 프로토타입·Gateway Agent), Step 3(일정·아키텍처·콜플로우·첫 프로토타입: IN-AE ↔ IN-CSE ↔ MN-CSE ↔ MN-AE)
- **리소스:** recipes.onem2m.org, acmecse.net, oneM2M Jupyter notebooks, oneM2M 개발자 문서

---

## 2. 프로젝트 파일 구조 (전체)

```
PSU_CAPSTONE_1S26/
├── README.md
├── .gitignore
├── docker-compose.yml              # CSE(8080), notebooks(8888)
├── acme_in/
│   ├── acme.ini                    # IN-CSE 설정 (id-in, cse-in, port 8080)
│   └── data/                       # ACME 런타임 데이터 (gitignore)
├── acme_mn1/, acme_mn2/            # MN-CSE 설정 (8081, 8082) – 현재 미사용
├── gatewayAgent/
│   ├── gatewayAgentReadMe.md
│   ├── setup.py                    # cse_url(8080), notification 9000, gatewayAgent
│   ├── main.py                     # 진입점: 알림서버 → orchestrator AE+컨테이너 → gatewayAgent AE+cmd/data+구독 → contentInstance → retrieve
│   ├── ae.py                       # register_AE, unregister_AE, retrieve_AE
│   ├── container.py                # create_container, retrieve_container
│   ├── contentInstance.py          # create_contentInstance, retrieve_contentinstance
│   ├── subscription.py             # create_subscription
│   ├── notificationReceiver.py     # POST 수신(9000), processData.process(data)
│   └── processData.py              # process(data) – 현재 pass
├── orchestrator/
│   ├── orchestratorReadMe.md
│   ├── requirements.txt            # Django, requests, docker, django-cors-headers, python-dotenv
│   ├── manage.py
│   ├── orchestrator/
│   │   ├── settings.py, urls.py, wsgi.py, asgi.py
│   │   └── __init__.py
│   └── ui/
│       ├── apps.py                 # ready(): initialize_AE_only(application_name)
│       ├── setup.py                # cse_url(8080), notification 7070, application_name='orchestrator'
│       ├── ae.py                   # register_AE(originator), unregister_AE; rn='orchestrator'
│       ├── views.py                # dashboard → dashboard.html, registration_status
│       ├── urls.py                 # "" → dashboard
│       ├── services.py             # initialize_AE_only, initalize_Full_startup
│       ├── container.py, contentInstance.py, subscription.py
│       ├── notificationReceiver.py # POST 수신(7070)
│       ├── templates/ui/
│       │   ├── base.html, dashboard.html
│       │   └── (Host/CSE/AE 모달 템플릿)
│       └── static/ui/
│           ├── app.js               # Provision Host / Add CSE / Deploy AE UI
│           └── styles.css
└── docs/
    └── PROJECT_OVERVIEW_AND_TESTING.md  # 이 문서
```

---

## 3. 연결 관계 요약

| 항목 | Orchestrator (Django) | Gateway Agent |
|------|----------------------|---------------|
| CSE | `http://localhost:8080/~/id-in/cse-in` | 동일 |
| AE 이름(경로) | `orchestrator` (동일 리소스) | `orchestrator` 생성·사용, `gatewayAgent` 생성·사용 |
| 알림 수신 포트 | 7070 | 9000 |
| 역할 | 시작 시 AE `orchestrator`만 등록 | orchestrator AE + cmd/data, gatewayAgent AE + cmd/data + 구독, contentInstance 생성 |

---

## 4. 테스트 방법

### 사전 조건

- Docker 설치 및 실행
- Python 3.9+ (orchestrator: Django, gatewayAgent: requests만 사용)
- 프로젝트 루트: `PSU_CAPSTONE_1S26`

### 4.1 IN-CSE만 띄우고 확인

**`The container name "/acme-in" is already in use` 에러가 나면:**  
이미 같은 이름의 컨테이너가 있으므로, 아래처럼 **먼저 제거**한 뒤 같은 `docker run`을 다시 실행하세요.

```bash
# 프로젝트 루트(PSU_CAPSTONE_1S26)에서 실행
docker rm -f acme-in 2>/dev/null
docker run -it -p 8080:8080 -e hostIPAddress=localhost -v ./acme_in:/data --name acme-in ankraft/acme-onem2m-cse:latest
```

- 터미널에 `CSE started` 나오면 성공.
- 다른 터미널에서: `curl -s http://localhost:8080/~/id-in/cse-in` → CSE 응답 확인.

### 4.2 Orchestrator (Django)만 띄우고 AE 등록 확인

1. IN-CSE가 **먼저** 8080에서 떠 있어야 함.
2. 실행:

```bash
cd orchestrator
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py runserver
```

3. 기대 동작:
   - 콘솔에 `IN-CSE response: Orchestrator AE successfully created` (또는 AE 등록 성공 메시지).
   - 브라우저 `http://127.0.0.1:8000/` → 대시보드, 상단/상태에 등록 상태 표시.
4. CSE에 리소스 확인:  
   `curl -s -X GET "http://localhost:8080/~/id-in/cse-in/orchestrator" -H "X-M2M-Origin: orchestrator" -H "X-M2M-RI: test1" -H "X-M2M-RVI: 4"`  
   → 200 + `m2m:ae` 등이 보이면 AE `orchestrator` 생성된 것.

### 4.3 Gateway Agent만 띄우고 전체 리소스 생성 확인

1. IN-CSE가 **먼저** 8080에서 떠 있어야 함.
2. (선택) Orchestrator를 먼저 띄우면 AE `orchestrator`가 이미 있어서, Gateway가 같은 AE를 다시 만들 때 **409 Conflict**가 날 수 있음. 그때는 Gateway 쪽에서 “이미 존재하면 무시” 처리하거나, **테스트 시에는 Orchestrator 없이 Gateway만** 실행해도 됨.
3. 실행:

```bash
cd gatewayAgent
pip install requests   # 필요 시
python3 main.py
```

4. 기대 동작:
   - `Starting notification receiver on port 9000`
   - `AE created successfully` (orchestrator, gatewayAgent)
   - `Container created successfully`, `Subscription created successfully`, `ContentInstance created successfully`, `Contentinstance retrieved successfully`
   - 에러 없이 대기 상태.
5. CSE 리소스 확인 예시:

```bash
# orchestrator 하위
curl -s "http://localhost:8080/~/id-in/cse-in/orchestrator" -H "X-M2M-Origin: Corchestrator" -H "X-M2M-RI: r1" -H "X-M2M-RVI: 4"
# gatewayAgent 하위
curl -s "http://localhost:8080/~/id-in/cse-in/gatewayAgent" -H "X-M2M-Origin: CgatewayAgent" -H "X-M2M-RI: r2" -H "X-M2M-RVI: 4"
```

### 4.4 통합 테스트 (권장 순서)

1. **IN-CSE 시작** (4.1)
2. **Orchestrator 시작** (4.2) → AE `orchestrator` 생성, 대시보드 확인
3. **Gateway Agent 시작** (4.3)  
   - 이미 `orchestrator` AE가 있으면 `register_AE('Corchestrator','orchestrator')`에서 409가 날 수 있음.  
   - 409가 나도 나머지(컨테이너, 구독, contentInstance)는 정상 동작할 수 있으므로, 터미널 로그와 curl로 리소스 존재 여부 확인.
4. **알림 테스트 (선택)**  
   - Gateway가 `gatewayAgent/cmd`에 구독해 두었으므로, 해당 컨테이너에 새 contentInstance를 만들면 CSE가 9000으로 NOTIFY를 보냄.  
   - Gateway 터미널에 `<= Subscription notification request received` 및 JSON 로그가 찍히면 알림 수신 성공.

### 4.5 Docker Compose로 CSE만 띄우기

```bash
docker-compose up -d cse
```

- CSE만 8080에 띄움 (볼륨 없음). 로컬 `acme_in` 설정을 쓰려면 `docker run`(4.1) 사용.

### 4.6 한 번에 따라 하는 테스트 (Quick Runbook)

**터미널 3개**를 열고 프로젝트 루트 `PSU_CAPSTONE_1S26`에서 아래 순서대로 실행하세요.

| 순서 | 터미널 | 할 일 | 성공 시 보이는 것 |
|------|--------|--------|-------------------|
| 1 | **터미널 1** | `docker rm -f acme-in 2>/dev/null; docker run -it -p 8080:8080 -e hostIPAddress=localhost -v ./acme_in:/data --name acme-in ankraft/acme-onem2m-cse:latest` | `CSE started` |
| 2 | **터미널 2** | `cd orchestrator && source venv/bin/activate && python manage.py runserver` (venv 없으면 `python -m venv venv` 후 `pip install -r requirements.txt`) | `AE created successfully`, `IN-CSE response: Orchestrator AE successfully created`, `Starting development server at http://127.0.0.1:8000/` |
| 3 | **터미널 3** | `cd gatewayAgent && python3 main.py` | `Starting notification receiver on port 9000`, `Contentinstance retrieved successfully` 후 **프로세스가 계속 떠 있음** |

**테스트 A – 브라우저에서 명령 보내기**

1. 브라우저에서 **http://127.0.0.1:8000/** 접속.
2. 왼쪽에서 **Deploy AE** 클릭 → **Deploy Sample AE *** 버튼 클릭.
3. 화면 상태란에 **"Command sent to Gateway"** 나오면 성공.
4. **터미널 3 (Gateway Agent)** 에 `<= Subscription notification request received` 와 `[processData] Received execute command from Orchestrator...` 가 찍히면 알림까지 성공.

**테스트 B – curl로 명령 보내기**

터미널 4(또는 아무 터미널)에서:

```bash
curl -X POST http://127.0.0.1:8000/api/gateway/command/ -H "Content-Type: application/json" -d '{"command":"execute"}'
```

- `{"success": true, "message": "Command sent"}` 가 나오고, **터미널 3**에 알림 로그가 찍히면 성공.

**테스트 C – API 상태 확인**

```bash
curl -s http://127.0.0.1:8000/api/status/
```

- `registration_status`, `cse_url` 이 JSON으로 나오면 정상.

**테스트 D – MN-CSE 이름을 Gateway data로 보내기 (Add CSE 화면)**

1. 터미널 1·2·3이 위 표대로 떠 있는 상태에서 진행.
2. 브라우저 **http://127.0.0.1:8000/** → 왼쪽 **Add CSE** 클릭.
3. **CSE Name** 입력란에 MN-CSE 이름 입력 (예: `acme-mn2`).
4. **Deploy CSE ACME *** 버튼 클릭.
5. 상태란에 **"MN-CSE name sent to Gateway"** 나오면 성공.
6. **터미널 3 (Gateway Agent)** 에 `<= Subscription notification request received` 및 `[processData] Received data: acme-mn2` (또는 입력한 값) 가 찍히면 Gateway가 data 알림을 받은 것.

**curl로 같은 동작 테스트:**

```bash
curl -X POST http://127.0.0.1:8000/api/gateway/data/ -H "Content-Type: application/json" -d '{"data":"acme-mn2"}'
```

- `{"success": true, "message": "Data sent"}` 이고 터미널 3에 알림 로그가 나오면 성공.

**테스트 E – Orchestrator가 gatewayAgent/data 구독으로 알림 받기**

1. Django(터미널 2) 기동 시 로그에 **"Orchestrator subscribed to gatewayAgent/data (notifications on port 7070)"** 가 있으면 구독 성공.
2. 위 **테스트 D** 또는 curl로 `gatewayAgent/data`에 content instance를 만들면, **터미널 2 (Orchestrator)** 에 `<= Subscription notification request received` 및 JSON 페이로드가 찍힘 (Orchestrator가 7070으로 NOTIFY 수신).

---

## 5. 코드 위치 요약 (어디에 어떻게 넣었는지)

| 기능 | 코드 위치 | 설명 |
|------|-----------|------|
| MN-CSE 이름 → Gateway data (UI) | `orchestrator/ui/static/ui/app.js` | `sendDataToGateway()`, `bindCSE()` 안 `deploy_cse_acme` 클릭 시 `fetch("/api/gateway/data/", { body: JSON.stringify({ data: mnCseName }) })` |
| MN-CSE 이름 → Gateway data (API) | `orchestrator/ui/api_views.py` | `api_gateway_data()` → `services.send_data_to_gateway(content)` |
| Gateway data에 contentInstance 생성 | `orchestrator/ui/services.py` | `send_data_to_gateway(content)` → `create_contentInstance_with_response(..., gateway_data_path, content)` |
| Orchestrator가 gatewayAgent/data 구독 | `orchestrator/ui/services.py` | `subscribe_to_gateway_data()`: `run_notification_receiver()` 후 `create_subscription(..., gateway_data_path, "orchestratorSubToGatewayData", notificationURIs)` |
| Orchestrator 시작 시 구독 실행 | `orchestrator/ui/services.py` | `initialize_AE_only()` 마지막에 `subscribe_to_gateway_data()` 호출 |
| Orchestrator 알림 수신 (7070) | `orchestrator/ui/notificationReceiver.py` | POST 수신 시 `<= Subscription notification request received` 및 payload 출력 |
| Gateway가 data 알림 처리 | `gatewayAgent/processData.py` | `process(data)` 에서 `con` 이 "execute"가 아니면 `[processData] Received data: ...` 출력 |

---

## 6. 알려진 이슈·참고

- **Orchestrator 먼저 vs Gateway 먼저:** 둘 다 AE `orchestrator`를 만들 수 있어서, 순서에 따라 한쪽에서 409가 발생할 수 있음. 409 시 “already exists”로 간주하고 진행하도록 한쪽에서 처리하면 편함.
- **알림 URI:** Gateway는 `http://host.docker.internal:9000` 사용. CSE가 Docker 안에 있으면 host.docker.internal으로 호스트의 9000에 접근. 로컬에서만 테스트할 때는 CSE·Gateway 모두 호스트에서 돌리면 `localhost:9000`으로도 동작 가능.
- **processData.process():** Gateway가 알림을 받으면 호출되지만 현재는 `pass`라, 이후 여기서 cmd/data 처리·config 반영·재시작 로직을 넣을 수 있음.

이 문서는 Kickoff pptx 내용과 현재 코드 기준으로 작성했으며, 추후 단계(Step 2/3)에 맞춰 단계별 테스트를 추가하면 됩니다.
