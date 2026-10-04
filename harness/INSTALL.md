# 프로젝트에 설치하고 GitHub에서 업데이트하기

공식 배포 저장소: https://github.com/meong99/Blender-Harness

## 최초 설치

최신 Release의 `blenderwright-harness-v<버전>.zip`을 내려받아 프로젝트 밖 임시 폴더에 푼다. 그 폴더에서 실행한다. 대상 프로젝트는 이미 존재하는 폴더여야 한다.

```powershell
.\harness.ps1 install --project 'C:\MyGame' --repo meong99/Blender-Harness
```

현재 풀어 놓은 버전을 오프라인으로 설치하려면 `--repo`를 생략한다. 이후 첫 원격 업데이트에 `--repo meong99/Blender-Harness`를 지정하면 저장소가 기록된다. Blender를 실행하지 않는 설치라도 Windows launcher는 Blender 내장 Python을 사용하므로 Blender 설치가 필요하다. 일반 Python 3.10 이상이 있으면 `python harness/cli.py install ...`도 가능하다.

설치 결과:

```text
MyGame/
  AGENTS.md                 # 원문 유지 + Blender 안내 관리 구역
  기존 프로젝트 파일들      # 유지
  .blender-harness/
    harness.ps1
    AGENTS.md               # 하네스 폴더 전용 규칙
    harness/                # 공통 실행·검수·설치기
    templates/
    vendor/
    .install.json           # 설치 버전·배포 파일 해시·저장소
    .backups/               # 변경 전 파일과 journal.json
    runs/                   # 제작 결과·프리뷰·기록
```

프로젝트를 에이전트에서 열고 이미지와 “이 사진처럼 만들어줘”라고 요청하면 된다. 코딩 에이전트가 루트 AGENTS.md를 읽는 환경이 전제다. 기존 프로젝트의 폴더별 규칙도 준수한다.

## 다음 버전 받기

프로젝트 루트에서:

```powershell
.\.blender-harness\harness.ps1 check-update
.\.blender-harness\harness.ps1 update --dry-run
.\.blender-harness\harness.ps1 update
```

`check-update`는 최신 정식 Release 정보를 읽는다. `update`는 ZIP의 GitHub SHA256과 내부 파일 해시를 확인한 뒤 적용한다. 코드 커밋만 올라온 상태는 배포로 취급하지 않는다. 예약 확인·백그라운드 자동 업데이트는 없다. 사용자는 에이전트에게 “하네스 업데이트해줘”라고 말해도 된다.

오프라인 패치:

```powershell
.\.blender-harness\harness.ps1 update --package 'C:\Downloads\blenderwright-harness-v1.2.1.zip'
```

이 버전명은 다음 배포 예시다. 실제 받은 파일 이름을 사용한다. v1.0/v1.1 ZIP에는 설치 manifest가 없으므로 이 설치기로 바로 업데이트할 수 없다. 기존 폴더는 보존하고 v1.2 이상 설치기를 새로 사용한다. 과거 제작 결과를 자동 이전하지 않는다.

## 병합 규칙

- 기존 AGENTS.md의 관리 구역 밖은 BOM·줄바꿈을 포함해 그대로 보존한다. 하네스 관리 구역은 하나만 유지한다. 추가 규칙은 구역 밖에 적는다.
- 사용자 지시와 기존 프로젝트 규칙이 하네스 기본값보다 우선한다. 서로 모순되는 중요한 요구는 에이전트가 확인한다. 설치기가 자연어 규칙의 의미적 충돌을 완전히 판정하지는 않는다.
- 배포 파일이 로컬에서만 바뀌었으면 유지한다. 같은 파일이 새 버전에서도 바뀌었으면 충돌 경로를 출력하고 아무 파일도 적용하지 않는다. 에이전트에게 두 변경을 비교·병합하도록 요청한다. 무조건 덮어쓰기 옵션은 제공하지 않는다.
- `runs/`와 기존 프로젝트 파일은 업데이트 대상이 아니다. 제작이 진행 중이면 먼저 완료한다.
- 기존 AGENTS.md는 UTF-8 또는 UTF-8 BOM을 지원한다. UTF-16은 변경하지 않고 중단한다. 심볼릭 링크/정션 경로 및 프로젝트 밖으로 나가는 경로는 관리하지 않는다.
- `.backups/<기록>/files/`와 `journal.json`에 변경 전 내용이 남는다. 쓰기 오류는 복원하지만 프로세스 강제 종료/전원 중단은 수동 복구가 필요할 수 있다. journal의 null 항목은 당시 없던 파일이다.

공개 저장소는 인증 없이 받을 수 있다. 비공개로 바꾸면 실행 환경의 `GH_TOKEN` 또는 `GITHUB_TOKEN`에 읽기 권한을 가진 자격 증명이 필요하다. 토큰은 파일·AGENTS·명령 인수에 저장하지 않는다. 이 설치기는 github.com을 지원하며 Enterprise 호스트는 미지원이다. 저장소를 신뢰하는 것이 전제이며 해시는 게시자 신원을 독립 서명으로 검증하는 수단이 아니다.

## 유지보수자가 새 버전 배포하기

1. `harness/defaults.json`의 version과 CHANGELOG/관련 규칙을 함께 갱신한다.
2. 테스트 후 코드 변경을 저장소에 커밋하고 같은 버전의 `vX.Y.Z` 태그를 푸시한다.
3. `.github/workflows/release.yml`이 테스트, bundle, GitHub Release 생성을 수행한다. 하네스 코드·규칙·예제·백엔드·라이선스만 ZIP에 포함한다.
4. Release 성공을 확인한 뒤 설치 프로젝트에서 `check-update`와 `update`를 실행한다.

GitHub API 근거: [Releases](https://docs.github.com/en/rest/releases/releases), [Release assets](https://docs.github.com/en/rest/releases/assets).
