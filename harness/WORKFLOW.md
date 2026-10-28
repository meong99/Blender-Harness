# 공통 제작 절차 v1.4.0

## 1. 공통 작업 규칙과 진행 순서

제작 규칙은 아래 동봉된 스킬 문서를 읽고 적용한다. 배포본과 전역 스킬이 다르면 사용자·프로젝트 지침을 우선하며, 이 하네스 작업에는 동봉본을 적용한다. 이 문서는 실행 명령, 모델 코드 계약, 검수 기록 형식과 상태 전이를 담당한다.

| 작업 단계 | 규칙의 단일 출처 |
| --- | --- |
| 시안 생성·월드 스타일 비교 | [zepeto-asset-pipeline](skill-zepeto-asset-pipeline.md) |
| 복구 이력 → 제작 기준·트라이앵글 예산 → 파트·내부 설계 → 블록아웃 → 표면·UV → 조립·시각 검수 → 내보내기·저장 | [blender-workflow](skill-blender-workflow.md) |
| Unity 통합·카메라 충돌·스플라인 배치 | [zepeto-unity-workflow](skill-zepeto-unity-workflow.md) (Unity 작업이 범위에 있을 때) |
| 버그 수정 방법과 검증 이력 | 프로젝트 `.zepeto-harness/bug-fix-playbook/` |

신규 제작은 시안 준비 후 품질 계획과 실행을 생성한다. 기존 작업 수정은 해당 실행의 기록과 수정 대상부터 확인한다.

## 2. 주요 용어

| 용어 | 뜻 |
| --- | --- |
| 기본 형태 단계 (`body`) | 시안을 바탕으로 전체 실루엣·비율과 주요 파트의 형태·배치를 잡는 단계. |
| 디테일 단계 (`detail`) | 기본 형태에 세부 형상·재질·텍스처를 추가하는 단계. |
| 수정 단계 (`edit`) | 검수에서 발견한 문제나 사용자 피드백을 반영하는 단계. |
| 최종화 단계 (`final`) | 검수한 결과의 최종 렌더·저장·확인을 수행하는 단계. |
| 실행 (`run`)·실행 ID | 하나의 제작 작업과 그 작업을 구분하는 고유 번호. |
| 리비전·체크포인트 (`revision`) | 실행 안에서 단계별로 저장한 작업본. 별도 정식 에셋이 아닌 검수·수정용 기록. |
| 기준 작업본 (`base`) | 다음 제작·수정 단계에서 불러와 이어서 작업할 리비전. |
| 품질 계획 (`quality-plan`) | 제작 전에 정한 재현 대상, 연결·분리 조건, 검수 시점과 비교 기준. |
| 검수 (`review`)·검수 기록 (`visual-review`) | 실제 모델의 렌더를 확인하고 결과·결함·증거 이미지를 기록하는 절차와 자료. |
| 작업 기록 (`manifest.json`) | 요청·설정·리비전·검수 결과·진행 상태를 저장하는 파일. |
| 프리뷰·클레이 렌더 | 프리뷰는 검수용 이미지이며, 클레이 렌더는 텍스처 대신 단색 재질로 형태를 보여주는 이미지. |
| 해시 (`hash`) | 파일 내용이 바뀌었는지 확인하는 값. 모델의 품질 점수는 아님. |

## 3. 요청 처리와 실행 설정

사용자가 대상과 참고 이미지만 주어도 진행한다. 이미지에서 실루엣, 비율, 특징 부품, 재질을 추출해 제작 우선순위를 짧게 기록한다. 중요하고 추정 불가능한 조건만 질문한다. 사용자가 추가 조건을 주면 기본값보다 우선한다.

기본값의 단일 출처는 `harness/defaults.json`이다. 사용자 요청은 실행별 manifest의 request와 설정에 남긴다. 설정 변경은 새 실행을 만들기 전에 적용하고, 실행 중인 설정 스냅샷은 유지한다.

## 4. 품질 계획 작성

에이전트가 `templates/quality-plan.json`을 참고하여 품질 계획을 작성하고 new에 `--quality-plan <계획.json>`을 전달한다. review에는 `--surface-notes <접합부 검수>`와 `--reference-notes <시안 비교 또는 해당 없음 사유>`를 함께 전달한다. 사용자가 JSON이나 긴 프롬프트를 작성할 필요는 없다.

시안의 형태가 최종 판단 기준이다. 단면 오차, 연결 성분, 열린 경계 등의 수치는 보조 자료이며 시각적 불일치를 상쇄하지 않는다.

제작 전에 quality-plan의 `visual_requirements`에 시안에서 반드시 재현할 부위별 실루엣·볼륨·접합부를 적는다. 전체 바운딩 박스만으로 대신하지 않는다. 각 항목에 고유 id, 구체적인 `expected`, 서로 다른 카메라의 품질 view 이름 두 개 이상, 입력 이미지가 있으면 `reference_indices`를 지정한다. 이 계획은 기존 계획과 함께 해시로 고정된다.

### 표면 연결과 시안 비교

- `intent`: 연결될 부분, 분리할 부분, 의도한 틈의 판단과 가정을 기록한다. 사용자가 분리·가동을 명시하면 우선한다. 합치면 중요한 기능이 달라지는데 시안이 모호할 때만 질문한다.
- `continuous`: name, objects(정확한 메시 이름), closed(닫힌 표면 요구 여부). 평가된 메시에서 연결 성분 합이 1이어야 한다. closed=true일 때 non-manifold edge도 0이어야 한다. 모든 모델의 구멍을 막으라는 규칙이 아니다.
- `separate`: 서로 다른 오브젝트로 남아야 할 이름들을 한 그룹에 기록한다. 예: Vase와 Badge, Box와 Lid. 부품을 합쳐 지정한 오브젝트가 사라지면 사후 검사에서 실패한다. 이름만 남긴 가짜 부품이나 실제 가동 간격을 검증하는 보안/물리 검사기는 아니다.
- `views`: 최대 3개 고정 카메라. location/target/type과 ORTHO의 ortho_scale 또는 PERSP의 lens를 지정한다. role=joint는 접합부 확대, role=reference는 시안 비교다. continuous가 있으면 joint가 필요하고, 입력 이미지가 있으면 reference가 필요하다.
- reference에는 reference_index(입력 순서, 0부터), 촬영 조건/측정 근거 provenance, landmarks를 지정한다. landmark는 name/object/anchor/uv/tolerance_px를 갖는다. anchor는 평가된 월드 바운딩 박스 안의 0..1 위치, uv는 시안 좌상단 원점 0..1이다. 현재 기능은 부품 크기·위치 비교이며 임의의 표면 특징점이나 전체 실루엣 자동 매칭은 아니다.
- 시안과 같은 프레임·비율의 카메라를 맞추고 비교한다. 사진 촬영 조건을 모르면 추정이라고 기록하고 허용 오차에 반영한다. 조명 차이를 픽셀 색상 차이로 품질 판정하지 않는다. 기본 추가 프리뷰는 640×640, 16샘플이다.
- 계획은 실행 생성 시 복사·해시 고정한다. 결과에 맞춰 기준점을 옮기지 않는다. 기준을 바꾸면 새 실행으로 구분한다.
- 시안 비교의 목표·측정 기준점과 오차는 JSON에 기록한다. 사용자 확인은 Blender에서 한다. 실제 이미지 검수 후 surface-notes/reference-notes를 기록한다. 수치 실패는 pass 불가, 수정 기준으로 쓸 때 partial과 결함을 기록한다.

## 5. 실행 생성

1. `new --name <이름> --request <요청과 가정> --reference <이미지> --quality-plan <계획.json>`로 실행 폴더를 만든다. reference는 반복 가능하다. 크기는 `--dimensions <폭> <깊이> <높이>`로 미터 단위를 지정한다.
2. 모델별 형상 코드만 작성한다. 실행기, 스튜디오, 저장 검사기, 보고기를 다시 작성하지 않는다.

아래 명령은 Windows에서는 `.\harness.ps1` 뒤에, 다른 환경에서는 `python3 harness/cli.py` 뒤에 붙인다. `new`가 출력한 실행 ID를 이후 `--run`에 사용한다.

## 6. 모델 코드 계약

`templates/example_asset.py`와 `harness/modeling.py`를 참고한다.

- `build_body(ctx)`, `add_details(ctx)`, `edit(ctx)` 중 해당 단계 함수를 제공한다.
- ctx에는 asset(ASSET 컬렉션)과 dimensions(미터 폭·깊이·높이 또는 None)가 들어온다.
- 모델 오브젝트는 ASSET에 넣는다. 앞은 -Y, 바닥 z=0, 중심 x=y=0을 기준으로 제작한다. STUDIO와 H_ 이름은 실행기가 소유한다.
- detail은 검수한 기본 형태를 보존하면서 부품을 추가한다. 필요하면 명시적인 edit에서 기존 부위를 고친다.
- 모든 실행은 별도 factory-startup Blender 프로세스에서 수행한다.
- 같은 실행에 동시 쓰기를 하지 않는다. 여러 자산은 실행 폴더와 프로세스를 분리한다.

## 7. 기본 형태·디테일 제작과 국소 수정

```text
stage --run ID --phase body --source builder.py
review --run ID --revision 001_body --decision pass --visual-review body-review.json --surface-notes "접합부 비교" --reference-notes "시안 비교" --notes "실루엣·비율·접지 검수 결과"
stage --run ID --phase detail --source builder.py --base 001_body
review --run ID --revision 002_detail --decision pass --visual-review detail-review.json --surface-notes "접합부 비교" --reference-notes "시안 비교" --notes "형상·재질·특징 검수 결과"
```

- 기본 형태 프리뷰는 512×568, 16샘플 클레이 앞·옆·뒤 3장이다.
- 검수 전이나 검수 후 파일·이미지 해시가 바뀌면 다음 단계는 실행되지 않는다.
- 디테일은 검수한 기본 형태 .blend에서 계속한다. 기본 컬러 사선 1장, 필요할 때 `--views hero back` 등 관련 시점만 최대 3장까지 지정한다.
- 수정이 필요하면 `review --decision revise`로 결함을 기록한다. 이 상태의 체크포인트는 다음 작업의 기준이 될 수 없으므로 보존 가능한 마지막 검수본을 사용한다. 결함을 인정하고 일부를 보존해 수정하려면 `partial`과 구체적인 결함을 기록하고 해당 체크포인트를 기준으로 삼는다.
- 국소 수정은 `stage --phase edit --base <검수본> --targets <정확한 오브젝트 이름들> --source builder.py`로 수행한다. 비대상 오브젝트의 평가 형상·변환·UV·주요 재질 설정 변경을 검사한다. 모든 Blender 데이터에 대한 완전한 의미적 동등성 검사는 아니다. 공용 재질 변경은 다른 오브젝트에도 영향을 줄 수 있다.

## 8. 시각 검수 기록과 수정 판정

1. `templates/visual-review.json`을 작업별로 작성하고 `review --visual-review <파일>`로 제출한다. `inspected_images`는 현재 프리뷰 전체, `requirements`는 고정 항목 전체를 정확히 한 번 포함한다. `requirements[].status` 값은 `pass`(통과), `fail`(불합격), `uncertain`(판단 보류)이다. 각 항목의 `observed`에는 실제 차이를, `evidence`에는 지정 시점들의 현재 렌더 경로를 적는다. 추가로 발견한 시각 결함은 고유 id와 관련 requirement를 가진 `defects`에 `open`으로 남긴다. 결함이 없으면 실제 확인 후 빈 목록을 쓴다.
2. 불합격/불확실 항목과 열린 결함은 수정 단계로 이어진다. `partial`은 보존할 수 있는 수정 출발점일 뿐 완료 승인이 아니다. 다음 검수에서 열린 결함을 누락할 수 없다. 해결 시 새로 달라진 체크포인트의 재검수 증거와 `repair: {"action": "구체적인 수정 내용", "before_images": ["이전 증거 경로 전체"]}`를 기록한다. 항목은 `pass`, 결함은 `resolved`로 판정한다.

## 9. 최종화와 완료 판정

`finalize`는 최신 검수본이 `pass`이고 필수 항목 전체 통과 및 미해결 결함 0개일 때만 실행된다. 이전 pass 검수본을 골라 이후의 결함을 우회할 수 없다. 최종 컬러/클레이 4장도 다시 검수하며 final의 `partial`/`revise`는 완료가 아니라 `needs_revision`이다. 최종 렌더에서 새 결함이 보이면 마지막 편집본을 기준으로 수정하고 다시 검수한다.

사용자가 명시적으로 범위를 바꾸지 않았다면 필수 결함을 ‘한계’, ‘추정’, ‘시간 부족’, ‘검수본’으로 재분류해서 완료하지 않는다. 자동 생성한 문구는 사용자 범위 변경의 증거가 아니다. 실제 범위 변경이 있을 때만 그 사용자 지시를 기록한 새 실행을 만든다. 스키마에는 임의 면제/waived 상태를 제공하지 않는다.

```text
finalize --run ID --base <검수한 detail 또는 edit ID>
review --run ID --revision <출력된 final ID> --decision pass --visual-review final-review.json --surface-notes "접합부 비교" --reference-notes "시안 비교" --notes "최종 컬러·클레이 4장 실제 검수 결과"
status --run ID
```

최종은 1080×1200, 64샘플 컬러 앞 사선·뒤와 클레이 앞 사선·뒤 4장이다. 저장본을 독립 프로세스에서 한 번 재열어 형상, 소스·참조 패킹을 확인한다. 같은 기준 파일의 finalize 재호출은 기존 결과를 반환한다. 최종 pass 검수 후에만 completed가 된다. partial은 needs_revision으로 남겨 수정한다. 실패 실행은 검수 통과로 바꿀 수 없다. 검수 증거의 해시를 유지하기 위해 추가 작업은 새 실행에서 한다. 실행별 체크포인트와 완료 실행의 보관·정리는 스킬의 에셋 파일과 복구 이력 규칙을 따른다.

## 10. 기록과 정식 에셋 인계

manifest.json, report.md, runs/CURRENT.md는 명령 실행 시 자동 갱신된다. .blend에 모델 소스와 참고 이미지를 패킹하고, 원본 코드·실패 로그·검수·해시를 실행 폴더에 보존한다. 실행 중인 검수 증거는 해시 검증에 사용한다. 정식 에셋 반영과 완료 실행의 보관·정리는 스킬의 에셋 파일과 복구 이력 규칙을 따른다.



새 제작마다 프로젝트 설계 문서를 다시 쓰지 않는다. 규칙 변경 때만 AGENTS/defaults/WORKFLOW와 관련 문서를 함께 갱신한다. 역사적 비교 보고서는 원래 기준을 유지한다.

## 11. 설치·업데이트와 배포

설치는 [INSTALL.md](INSTALL.md)를 따른다. 기존 프로젝트 루트에 ZIP 내용을 덮어쓰지 않는다. `install --project <경로>`는 `.blender-harness/`에 하네스를 격리하고, 루트 AGENTS.md의 기존 바이트를 보존하면서 관리 구역만 추가한다. 설치된 문서의 상대 경로는 `.blender-harness/` 기준이다. 기존 프로젝트 규칙과 사용자 지시를 우선하고 Blender 제작 요청에만 하네스를 적용한다.

`install --project <경로> --repo meong99/Blender-Harness`는 GitHub의 최신 정식 Release를 설치하고 업데이트 저장소를 기록한다. 설치 후 `check-update`는 버전만 확인하고, `update --dry-run`은 다운로드 검증 및 변경 계획만 출력하며, `update`가 실제 적용한다. 로컬 ZIP은 `update --package <ZIP>`으로 적용한다. 실행 중인 제작이 있으면 완료 또는 실패 상태가 된 뒤 업데이트한다.

업데이트는 관리 파일별 기존 배포 해시와 현재 파일 및 새 배포를 비교한다. 프로젝트의 비관리 파일과 `runs/`는 보존한다. 로컬만 바뀐 파일은 유지하고 양쪽이 다르게 바뀐 동일 파일이나 관리 구역 충돌은 전체 적용 전 중단한다. 코드 문장의 자동 의미 병합은 하지 않는다. 변경 파일은 `.backups/`에 저장하고 정상적인 쓰기 오류 시 이전 바이트로 복원한다. 전원 중단의 자동 복구까지 보장하지 않는다. 작업별 요구를 전역 규칙으로 바꾸지 않는다.



`bundle --out dist/blenderwright-harness-v1.4.0.zip`은 규칙·설정·코드·예제·blenderwright addon 및 라이선스만 묶는다. 참조·사용자 결과·세션 로그·Blender 실행 파일·다른 후보 설치는 제외한다. ZIP 내부 PACKAGE.json과 옆 manifest에 포함 파일과 해시가 저장된다. GitHub 태그와 defaults.json의 버전이 같을 때 Release workflow가 테스트 후 이 ZIP을 배포한다.
