# FastAPI AIP Example

## Introduce

[Google AIP(API Improvement Proposals)](https://google.aip.dev/general)에 등장하는 API 권장 설계 패턴을 구현한 예제 레포지토리입니다.

Swagger로 제공되는 API 문서에 구현된 기능에 대한 설명이 기록되어 있으니 [Install and Run](#install-and-run)을 수행하여 로컬 환경에서 어플리케이션을 실행해야 합니다.

## Install and Run

1. git clone을 활용해 해당 레포지토리를 클론합니다.
2. $ pip install -r requirements.txt
3. $ uvicorn example.entrypoints.fastapi_:app --realod
4. [localhost:8000/docs](http://localhost:8000/docs)에 접근