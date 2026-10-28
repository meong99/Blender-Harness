---
name: zepeto-unity-workflow
description: Modify and troubleshoot existing ZEPETO Unity scenes, avatar loading, SDK cameras and controls, gameplay scripts, lighting, materials, and asset integration while preserving saved layouts. Use for Unity integration and repair; use an asset-production skill for standalone modeling.
---

# ZEPETO Unity 작업

## 1. 시작과 적용

- 프로젝트 지침에서 활성 프로젝트·저장 씬·최신 기준을 확인한다. 과거 layout/Setup 생성기를 현재 씬 위에 재실행하지 않는다. 수동 배치, GUID, 원본 에셋, 프리팹 연결을 보존한다.
- 이미 로드된 에디터 bridge가 있으면 프로젝트에 기록된 요청/응답 절차를 사용한다. 소스보다 최신인 컴파일 결과와 적용 응답을 확인한다. bridge 미로드와 백그라운드 갱신 지연을 구분하고 창 활성화를 반복 요구하지 않는다. 요청받지 않은 Play 중단은 피한다.
- 에디터 보정은 프리팹 인스턴스 override와 씬/에셋 저장까지 반영한다. 일시적 런타임 변경이나 캡처용 상태를 영구 적용으로 보고하지 않는다.

## 2. SDK에서 확인할 점

- SDK 기본 카메라/모바일 컨트롤러를 쓰는 프로젝트에서는 사용자 요청 없이 추적/FOV/투영을 덮어쓰지 않는다. Touchpad 프리팹 연결뿐 아니라 useDefaultVirtualController를 확인한다.
- 아바타 생성 로더 중복, 로그인 사용자 취득 경로, 늦게 로드되는 의상을 확인한다. 계정 ID/인증정보는 진단 로그에서 제외한다.
- 설치된 SDK 타입/허용 API를 확인한다. 일부 ZEPETO TS 환경에서 Application.runInBackground는 ForbiddenType, Vector3==null은 native equality 오류를 일으켰다. 사용 중 버전에서 확인하고 boolean/참조 기반 분기를 택한다.
- 제스처가 시작되지 않으면 constraintStateAnimation 잠금과 이동 취소를 확인한다. 최적화된 다운로드 클립의 CopySerialized 결과는 빈 곡선일 수 있다. 파일 존재가 아닌 실제 재생/재열기로 판정한다.

## 3. 외관과 충돌체 정합성

- 광원 존재만 확인하지 말고 대상 Renderer 레이어, culling mask, shader/pass, 재질 blend, 품질 설정을 확인한다. 같은 구도의 실제 조명 on/off 렌더로 원인을 좁힌다. 특정 프로젝트의 조명 강도/색/레이어 번호를 다른 프로젝트에 강제하지 않는다.
- 캐릭터/대형 에셋 전용 레이어 변경은 시각 메시만 대상으로 한다. 컨트롤러·물리 루트까지 변경하면 충돌이 달라질 수 있다. 늦게 생성되는 메시와 종류 교체 후 마스크도 확인한다.
- 평평한 글자 정면의 삼각형 음영은 면 방향뿐 아니라 bevel과 공유된 노멀을 확인한다. 정면 노멀을 분리하고 옆면/모서리 형태를 보존한다. 분리 조각의 방향을 전체 합산 체적만으로 판정하지 않는다.
- 메시 결합 시 재질 submesh와 변환을 보존한다. 한 Mesh/Renderer가 한 draw call을 뜻하지 않는다.
- 충돌체가 이동한 렌더 메시를 따라가는 계층인지 확인한다. 모델 축 변환을 덮어쓰지 말고 필요한 회전을 합성한다.

## 4. 플레이어·카메라 충돌

- 건물·바닥 등 플레이어의 이동을 막는 오브젝트는 기본적으로 카메라도 막는다. 충돌체와 카메라 충돌 마스크가 해당 오브젝트를 포함하는지 확인한다.
- 스프링암 방식의 카메라 충돌 보정(Spring-arm Camera Collision)을 적용한다. 추적 대상과 카메라 사이의 장애물을 검사하고 카메라 거리를 조정해 벽을 관통하지 않도록 한다. 설치된 SDK 카메라의 충돌 기능 또는 지원 API로 구현하며, 기존 추적·FOV·투영 설정을 보존한다.

## 5. 스플라인 배치와 교차로

- 도로 등 같은 모듈을 일정 간격으로 배치하는 구조는 스플라인 기반 배치(Spline-based Placement)로 제작한다. 스플라인 시작점·끝점, 제어점과 내부 배치 데이터를 Inspector에서 수정할 수 있도록 노출한다.
- 3방향·4방향 분기는 교차로 접합부(Junction)를 고려해 구성한다. 직선 도로 메시를 그대로 중첩하지 않고 연결부의 중복 면을 제거하거나 분기용 모듈을 사용해 Z-fighting을 방지한다.
- 조립 메시와 배치용 프리팹 구성은 프로젝트 AGENTS.md의 모델 프리팹 공유 규칙을 따른다.

## 6. 검증과 인계

- 변경에 맞는 확인만 수행한다. 타입 진단, 저장/재열기, 에디터 렌더, Play, 빌드, 실제 모바일은 각각 별도 결과다. SDK의 기존 선언 오류를 제외한 진단을 전체 tsc 통과로 부르지 않는다.
- 라이팅은 픽셀 광원 수·그림자·실기 성능을 별도 확인 대상으로 기록한다. 정적 예쁜 렌더만으로 모바일 성능을 보장하지 않는다.
- 현재 상태는 프로젝트별 짧은 문서에 갱신하고 작업 증거/옛 결과는 버전 폴더에 둔다. 이 공용 스킬에는 특정 월드의 좌표·계정·완료 이력을 추가하지 않는다.
- 버그 수정 시 프로젝트의 `.zepeto-harness/bug-fix-playbook/`에서 기존 해결 기록을 확인하고, 새 증상·원인·수정 방법·검증 결과를 기록한다.
