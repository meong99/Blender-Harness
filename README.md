# Blender Modeling Harness

현재 버전: **1.2.0**. 기존 프로젝트의 AGENTS.md를 보존하는 설치·병합과 GitHub Release 업데이트를 지원한다. [설치·업데이트 안내](harness/INSTALL.md) · [변경 이력](harness/CHANGELOG.md). 연결 표면·분리 부품과 고정 카메라 시안 검수는 v1.1 규칙을 유지한다.

이 폴더를 코딩 에이전트에서 열고, 참고 이미지를 첨부해 **“이 사진처럼 만들어줘”**라고 요청한다. 원하는 크기나 특별한 조건이 있을 때만 덧붙이면 된다. 에이전트는 AGENTS.md를 읽고 공통 실행기로 제작·검수·기록한다.

## 준비

- Blender 설치. 현재 Windows / Blender 5.2.2 LTS에서 검증한다.
- 파일 읽기·쓰기, 명령 실행과 이미지 검수가 가능한 코딩 에이전트.
- 하네스 자체는 별도 모델 API를 호출하지 않는다. 자연어 해석과 모델링 코드 작성은 사용하는 코딩 에이전트가 담당한다.

Windows PowerShell:

```powershell
.\harness.ps1 doctor
```

다른 환경은 Python 3.10 이상으로 `python3 harness/cli.py doctor`를 실행한다. Blender가 자동으로 발견되지 않으면 `BLENDER_BIN` 환경 변수에 실행 파일 경로를 지정한다. macOS/Linux는 경로 지원만 구현했으며 실기 검증하지 않았다.

## 기본 동작

blenderwright → 몸체 3시점 검수 → 디테일 → 필요한 부위 수정 → 최종 컬러·클레이 4장 → 저장본 재열기 1회. 검수는 에이전트가 수행한다. 매 단계 사용자 승인을 요구하지 않는다.

기본 범위는 Blender 제작이다. Unity 검사와 내보내기는 별도 요청할 때 수행한다. 15분은 소프트 목표이며 품질이나 완료 시간을 보장하는 제한이 아니다. 토큰은 세션 사용량을 확인할 수 있을 때만 기록하며, 없으면 미계측으로 남긴다.

결과는 `runs/<실행명>/`에 저장한다. `runs/CURRENT.md`에서 최근 결과, 프리뷰, 단계별 시간, 검수 기록으로 이동한다.

기존 프로젝트에는 ZIP을 프로젝트 밖에 푼 뒤 `.\harness.ps1 install --project 'C:\MyGame' --repo meong99/Blender-Harness`를 실행한다. 프로젝트 루트에 ZIP 파일들을 덮어쓰지 않는다. 이후 프로젝트 안에서 `.\.blender-harness\harness.ps1 update`로 새 Release를 적용한다. 기존 모델·참고 사진·세션 로그·다른 후보 런타임은 ZIP에 포함하지 않는다.

실행 규칙: [WORKFLOW](harness/WORKFLOW.md) · 설정: [defaults.json](harness/defaults.json)
