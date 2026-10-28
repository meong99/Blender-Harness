---
name: blender-workflow
description: Inspect, edit, repair, export and save Blender scenes and game assets through available Blender tools. Use for direct Blender operations, including saving an open scene, without requiring image generation. Simple conceptual Blender questions do not require the editing workflow.
---

# Blender workflow

Blender에서 직접 제작한다. 승인된 시안과 아래 품질 기준을 유지한다. 신규 제작은 아래 순서로 진행하고, 기존 모델 수정·내보내기·저장은 해당 단계부터 적용한다.

## 1. 작업 환경과 현재 씬 확인

Read project rules and discover the actual Blender runtime and configured tools on this device. Verify the connection with a read-only call; inspect the current file path, dirty state, active scene, selection and mode. Do not replace an open unsaved scene before preserving it. Use installed tool schemas and APIs for the actual Blender version; do not install packages as part of this skill.

If live MCP is stopped, discover the configured launcher or installed Blender runtime and use background CLI in an isolated file with --python-exit-code 1. Do not replace an open scene or claim Blender is unavailable solely because the live port is disconnected.

## 2. 에셋 파일과 복구 이력

- 정식 에셋의 파일명과 경로는 고정한다. 작은 수정마다 v2/v3 등 별도 정식 파일을 만들지 않는다. 실제로 함께 사용할 별도 디자인·변형만 새 에셋으로 구분한다.
- 작업 전 로컬 Git 저장소와 대상 파일의 추적·커밋 상태를 확인한다. 로컬 Git이 있으면 관련 파일만 의미 있는 작업 단계마다 커밋해 이력을 관리한다. 원격 연결은 필수가 아니며, GitHub 미연결·오프라인이어도 로컬 커밋을 사용할 수 있다. 푸시는 사용자의 원격 작업 지시에 따른다.
- Git 저장소가 있다는 사실만으로 복구 가능하다고 판단하지 않는다. 작업 시작 상태의 대상 파일·외부 텍스처가 커밋 및 필요한 로컬 LFS 객체로 복구 가능한지 확인한다. 미커밋 작업 등 커밋으로 보존할 수 없는 상태는 먼저 로컬 백업한다. 다른 작업의 변경을 함께 커밋하지 않는다.
- 로컬 Git이 없으면 작업 시작 전 한 번 대상 원본과 연결된 텍스처를 정식 에셋과 분리된 백업 폴더에 보관한다. 열린 씬의 미저장 변경도 복구 가능한 상태로 저장한다. 이를 위해 Git 초기화나 원격 연결을 필수로 요구하지 않는다.
- 로컬 백업은 에셋별 최근 3개와 사용자가 확정한 주요 버전을 보관한다. 기존 백업의 최초 정리는 목록을 사용자와 확인한 뒤 진행한다. 복구 검증이 끝나지 않은 작업의 유일한 복구본이나 다른 작업의 파일을 삭제하지 않는다.
- 작업 중 임시 체크포인트·자동 백업·검수 렌더는 정식 에셋과 분리하고 Git 추적에서 제외한다. 재제작에 필요한 소스·설정·참조와 주요 검수 기록은 보존한다. 이미 추적된 파일은 ignore만으로 제외되지 않으므로 기존 이력을 임의 삭제하거나 재작성하지 않는다.
- 수정 후 실제 메시의 다각도 검수를 통과한 결과를 고정된 정식 경로에 반영하고 저장본을 확인한다. Unity 에셋 갱신 시 기존 .meta와 참조를 보존한다. Git 이력이나 로컬 백업은 복구 수단이며, 검수 전 결과로 정식 에셋을 무조건 덮어쓰지 않는다.
- 하네스 실행 폴더의 해시 고정 체크포인트는 검수 증거용 임시 작업본이다. 체크포인트를 매번 별도 정식 에셋으로 배포하지 않는다. 실행 중인 검수 증거는 유지하며, 완료 후 보관·정리는 위 복구 정책을 따른다. 이 정책은 자동 백업·커밋·정리 기능이 구현되었다는 의미가 아니며 에이전트가 실제 수행 및 확인해야 한다.

## 3. 기존 모델 수정 전 진단

Inspect the actual model before editing. Record the relevant dimensions, geometry, UVs, materials and visible defect; apply only the quality checks relevant to the requested change. Compare before/after views of the edited region. Check operator return status and actual geometry changes: a completed script or created file alone does not prove an edit succeeded.

- Inspect the textured mesh and an untextured solid/clay view before editing. Distinguish geometric relief from painted shadows and normal-map details. Identify stone ridges, crevice bottoms, wood bends, worn edges and intentional asymmetry that must survive.

Preserve the source blend and user's open scene. Secure a recoverable commit or local backup before editing; use isolated working copies when needed and import only the target asset collection.

## 4. 시안과 제작 기준

신규 모델링 전에 `imagegen` 스킬과 이미지 생성 툴로 제작 시안을 준비하고 실제 이미지를 확인한다. 이미 확보한 적합한 생성 시안은 재사용한다. ZEPETO 에셋의 시안 준비·스타일 비교는 [zepeto-asset-pipeline](skill-zepeto-asset-pipeline.md)을 따른다.

- 크기는 프로젝트의 아바타 스케일, 상호작용, 주변 오브젝트를 기준으로 정한다. 루트 피벗은 바닥 중심으로 두고 변환을 적용한다. 경첩 등 가동 부품의 피벗은 실제 회전축에 둔다. 카운터의 비균일 스케일이 분리 소품에 전파되어 원형 바구니 등이 늘어나지 않도록 한다.
- ZEPETO 에셋은 복잡도에 따라 Low / Mid / High 중 트라이앵글 예산(Triangle Budget)을 선택한다. 기준은 최종 조립 오브젝트를 내보낼 때의 삼각형 수이며, 개별 가동 파트도 합산한다. Blender 편집 면 수와 구분한다.

| 등급 | 삼각형 수 기준 |
| --- | --- |
| Low | 500–5,000 |
| Mid | 최대 15,000 |
| High | 최대 30,000 |
| 예외: 랜드마크·기타 고밀도 에셋 | 최대 100,000 |

선택한 등급과 예산을 작업 계획에 명시한다. 위 기준을 벗어나는 경우에는 사용자 동의를 구한다.

## 5. 파트 분할과 내부 구조

파트 분할(Asset Decomposition)은 다음 기준으로 정한다.

1. 현실에서 하나의 완제품으로 취급되는 물건.
2. 다른 맵에서도 재사용할 수 있는 독립 에셋.
3. 절차적 콘텐츠 생성(PCG)에 쓰는 모듈 단위.
4. 사용자가 개별 움직임을 지정한 가동 파트(예: 열리는 문).
5. 구조가 복잡해 완성도가 떨어질 우려가 있으면 제작용 서브파트로 더 세분화하고, 형태 완성 후 필요한 단위로 병합한다.

빈 공간이 있는 오브젝트는 플레이어가 내부에 진입할 수 있는지 먼저 구분한다. 진입 가능한 구조는 필요한 내부를 구현하고, 진입하지 않는 구조는 불필요한 내부 지오메트리로 예산을 소모하지 않는다.

## 6. 블록아웃과 형태 정교화

- 기본 방식은 박스 모델링(Box Modeling)이다. 큐브·스피어 등 프리미티브에서 시작해 필요한 면을 분할하고 익스트루드(Extrude)로 형태를 만든다. 복잡한 구조는 위 파트 분할 기준에 따라 서브파트로 제작한 뒤 병합한다.
- 모든 신규 모델은 시안의 실루엣과 비율을 잡는 로우폴리 블록아웃(Blockout)부터 시작한다. 초기 밀도는 파트의 복잡도와 시안 형태를 유지하는 데 필요한 수준으로 정한다.
- 블록아웃 이후 필요한 부위의 지오메트리를 점진적으로 늘려 시안의 형태에 맞춘다. 처음부터 고밀도 메시로 시작하지 않는다.

## 7. 표면 표현과 UV 매핑

- 실루엣에 영향을 거의 주지 않는 얕은 요철·표면 무늬·평면 문양은 지오메트리 대신 텍스처로 표현한다.
- 텍스처는 `imagegen` 스킬과 이미지 생성 툴로 제작하여 적용한다. 주 해상도는 256×256–512×512이며, 필요할 때만 최대 1024×1024를 사용한다.
- 돌출된 구조라도 시각적으로 무리가 없고 효율적이면 노멀 맵(Normal Map), 범프 맵(Bump Map), 하이트 맵(Height Map) 등 표면 표현 기법을 활용한다. 대상 렌더러·셰이더가 지원하는 방식으로 적용한다.
- 모든 요철을 텍스처로 대체하지 않는다. 플레이어에게 보이는 정도, 실루엣, 메시 복잡도와 반복 요소를 기준으로 지오메트리와 텍스처 중 적절한 표현을 선택한다.
- 서로 다른 표면을 사용하는 부품은 면 그룹(Face Group)과 UV 아일랜드·텍스처 영역을 명확히 구분한다. 트레이 면이 소시지 텍스처 영역을 참조하는 등 의도하지 않은 공유·겹침을 금지한다.

## 8. 조립과 다각도 시각 검수

- 모든 파트를 제작한 뒤 최종 오브젝트로 조립한다. 파트 간 의도하지 않은 겹침·관통이 없도록 배치한다.
- 가동 파트는 전체 동작 범위에서 부품 간 여유 간격(Clearance)을 확인한다.
- 외부에 드러나는 면의 중첩을 검사한다. 동일 평면의 겹침(Coplanar Overlap)이나 같은 깊이의 평행한 면에서 발생하는 Z-fighting을 방지한다. 중복 면 제거 또는 의도한 접합 구조에 맞는 배치 조정으로 해결한다.

명백한 구멍·관통·접합 오류가 있으면 검수를 통과시키지 않는다.

검수 단계에서는 현재 작업본의 실제 메시를 여러 각도에서 렌더하고, 생성된 이미지를 직접 열어 실제 결함 여부를 판단한다. 정면·후면·좌우·위·아래 중 형상을 확인하는 데 필요한 시점을 사용하며, 접합부나 의심 부위는 확대 및 다른 각도로 추가 촬영한다. 텍스처가 형상을 가릴 수 있으면 클레이 렌더도 함께 확인한다. 한 시점에서 보이지 않는다는 이유로 결함이 없다고 판단하지 않으며, 가려져 확인할 수 없는 부위는 시점을 바꿔 확인한다. 의도한 구멍·틈·분리 구조와 제작 오류를 구분한다. 메시 수치나 검수 기록만으로 이미지 확인을 대신하지 않는다. 수정 후에는 수정 부위와 주변을 다시 촬영해 결함 해소 및 새 결함 발생 여부를 확인한다.

수정의 한계는 명확히 알린다. 게임 렌더용 메시가 반드시 3D 프린팅용 수밀 메시(Watertight Mesh)일 필요는 없다.

## 9. 요청된 내보내기

Export only the intended asset collection/selection and verify the active scene. Exclude presentation cameras, lights and floors unless requested. Check axis, units, pivots, materials and texture paths in a reimported export. Report exported triangles separately from Blender editing faces. An export does not replace saving the editable .blend source.

최종 메시 구성과 프리팹 단위는 프로젝트 AGENTS.md의 모델 프리팹 공유 규칙을 따른다.

## 10. 저장과 인계

- 작업이 완료되면 별도 요청 없이 저장하고, 정상 저장 여부를 확인한다.
- 모델과 수정한 텍스처를 함께 저장한다. 텍스처는 기본적으로 외부 파일로 관리하고, 전달용 단일 파일이 필요할 때 .blend에 포함한다.
- 결과 전달 시 저장 경로를 알리고, 저장에 실패하면 실패 내용을 보고한다.
