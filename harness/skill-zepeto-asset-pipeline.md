---
name: zepeto-asset-pipeline
description: Create and revise ZEPETO game assets directly in Blender from concept images, with Blender-based visual review and optional Unity integration.
---

# ZEPETO asset production and review

## 1. 적용 범위와 프로젝트 기준

Use Blender directly for modeling. Preserve approved concepts, separate-part requirements, assembly dimensions and all visual quality gates.

Read the project's AGENTS.md, development rules, performance budget, and current asset plan. Separate current implementation from old design drafts. Existing accepted assets are style references, not permission to redesign them.

- Asset production covers local Blender construction, inspection and delivery within the requested scope.
- User feedback is stored per model version. Preserve annotations and recoverable history using the Blender workflow asset recovery policy. Fixes update the canonical asset path after review; do not create a new canonical filename for every edit.

## 2. 환경 확인과 Blender 스킬 연결

Discover actual project paths, Python/Blender runtimes, and callable tools needed for the requested workflow. Verify connections with a read-only call. Do not install new packages or hardcode a previous device's executable path. Never read or expose credentials; use the configured launcher. If live Blender MCP is unavailable, discover the installed executable/configured launcher and use an isolated background process; a stopped live connection does not mean the skill is missing.

Before Blender inspection, editing, export or saving, read [blender-workflow](skill-blender-workflow.md). It owns mesh/texture quality gates, conservative cleanup and editable-source saving. Use the project's accepted cleanup reference.

## 3. 시안 준비와 월드 스타일 비교

- A modeling request means producing the requested 3D asset through inspection, repair, editable-source saving and review; do not stop at another concept sheet. A concept-only request remains image-only.
- World-based modeling follows this required order: inspect the approved world image and crop the target as a source reference; prepare clear standalone modeling concepts with the image-generation tool before new modeling; inspect those concepts; then construct the asset directly in Blender using the Blender workflow and project modeling harness. A tiny, blurred, occluded or neighbor-contaminated world crop is not a sufficient detail reference, and resizing alone does not recover missing detail. Preserve the approved design rather than inventing a new object. Reuse already adequate standalone concepts generated for the approved design.
- References: reuse clear approved concepts. For complex or hidden construction, prepare additional consistent views when needed to resolve geometry; distinguish inferred hidden surfaces from observed features. Additional views must preserve the same object, proportions, colors and details. Inspect and repair contradictions before modeling.
- Separate moving/reusable parts in the brief. Verify actual mesh separation and recessed surfaces after generation; tool names or painted shading are not proof.

### World-wide visual consistency gate

Compare across the whole world's asset set, including unrelated structures and categories (buildings, trees, rocks, props); same-category or same-material comparisons alone are insufficient.

- Before generating a concept, actually inspect representative user-approved world images and use them as visual references. If the user has delegated concept approval, clearly identify the provisional parent-approved baseline. A repeated style prompt alone is not a substitute for shared image references.
- After generation, view the candidate alongside those fixed baseline images and the other concepts in the current batch. Compare hue relationships, saturation, value range, contrast, detail density, shape simplification/faceting and material gloss. Preserve each object's functional silhouette and characteristic colors while checking that the set looks like one world. Do not let successive candidates gradually replace the fixed baseline.
- Record reference image paths and an explicit style/tone accept-or-revise verdict, separate from structural correctness. When an independent reviewer is authorized, give them the same comparison set; the parent must also inspect it. Do not create extra agents solely because this gate exists.
- Resolve concept mismatches before modeling. Apply this gate in autonomous mode too. Repeat the comparison on actual Blender model renders; a sound mesh can still fail the world's visual style.

## 4. 순차 제작 흐름

1. **Brief:** purpose, gameplay function, silhouette, reference style, dimensions, part boundaries, pivot, collider needs, priority, and tentative geometry/material budgets. Do not add new gameplay to justify props.
2. **References:** when requested, research actual construction/appearance on the web, open sources, and record links. Use references for structural understanding, not copying a third-party asset. Separate observed facts from design suggestions.
3. **Concepts:** reuse approved references as above; prepare the modeling concept with the imagegen skill/tool before new modeling; reuse adequate generated concepts and correct them when needed. Create consistent front/back/left/right references where useful. Reference the same approved design across views; do not invent new variants per direction. Keep independent props separable in the brief. Save images and prompts in the project.
4. **Independent review:** when the user authorizes agents, delegate a bounded image review to a separate agent with the brief and image files, not the desired verdict. Require actual visual inspection, silhouette/structure/view consistency, style fit, and game readability findings. The parent also views the images and records accept/revise with reasons. Do not call a sequential self-review an independent agent review. If delegation is unavailable, disclose and follow the user's allowed fallback; do not silently omit a required gate.
5. **Blender construction:** model directly from the approved concepts. Follow the Blender skill in order: triangle budget and interior access → part decomposition → low-poly blockout and progressive refinement → textures and UVs → assembly; establish dimensions, origins and mating interfaces before constructing separate parts; measure the resulting meshes and verify assembled fit. Use the Blender workflow and project modeling harness for editable source files, renders and iterative visual review.
6. **Mesh inspection:** open the actual model in Blender, count triangles/materials/textures, inspect all sides and underside, verify scale and structure. Treat UV-split vertices differently from physical holes. Render the actual model; do not use the concept image as evidence of mesh quality.
7. **Repair or retry:** revise topology, shape, surface detail, UVs, scale and pivots directly in Blender until the applicable concept-match gates are satisfied.
8. **Review and delivery:** review the asset in Blender and inspect actual multiview renders. Save passed results to stable canonical paths using the Blender workflow recovery and retention policy. An HTML/web viewer is not a required delivery. If an annotated web review is specifically requested, export asset-only GLB with selection and active-scene filtering; keep snapshots separate, preserve pins with their reviewed geometry, inspect the real web rendering and test changed review functionality.
9. **Optional Unity:** only when in scope; follow [zepeto-unity-workflow](skill-zepeto-unity-workflow.md) for camera collision, spline placement and integration. Apply the project AGENTS.md prefab-sharing rules. Keep originals under AIGenerated, runtime wrapper prefabs under the actual loader path; avoid duplicated runtime and scene instances. Check texture/normal imports, materials, scale, collider, prefab and scene references/mtime, console and actual rendering. Distinguish editor verification from mobile verification. No new Unity packages without permission.

## 5. 피드백 반영과 버그 수정 기록

When version-specific annotations exist, apply the following to the matching reviewed geometry.

Read the matching version's annotations, including text, position, normal, camera and target. For glTF exported through the tested Blender path, Blender coordinates are (x,-z,y); verify if the export transform changed. Do not transfer pins across changed origins/scales or silently mark user feedback resolved. Publish a per-note implementation record with before/after screenshots for user review.


ZEPETO 프로젝트의 버그 수정은 기존 `.zepeto-harness/bug-fix-playbook/`에서 관련 기록을 먼저 확인하고, 수정 후 증상·원인·해결 방법·검증 결과를 해당 플레이북에 기록한다.

## 6. 저장과 인계

Apply the Blender skill's save verification before handoff. For Unity integration, save modified scenes/assets and verify their on-disk state after leaving Play mode; runtime-only changes are not saved authoring results.

For each asset record: reference sources, brief, concept files/prompts, reviewer verdicts, original and repaired files, measured mesh stats, repair notes, preview images, review version and unresolved issues. Report concrete completion states: Blender-modeled / Blender-repaired / web-reviewed / Unity-imported / mobile-tested.

Never promise continuous execution after a turn without an actual continuation mechanism.
