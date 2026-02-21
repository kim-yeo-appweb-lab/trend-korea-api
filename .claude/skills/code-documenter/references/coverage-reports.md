# 커버리지 리포트

## 리포트 템플릿

```markdown
# 문서화 리포트: Trend Korea API

## 요약
- **분석 파일**: N개
- **Endpoint 문서화**: N/N (100%)
- **Pydantic Schema 문서화**: N/N (100%)
- **Service/Repository**: 자명한 메서드 제외, N개 문서화 추가

## 변경 파일

| 파일 | 변경 내용 |
|------|----------|
| src/trend_korea/api/routers/v1/xxx.py | summary, description, responses 추가 |
| src/trend_korea/api/schemas/xxx.py | Field description, examples 추가 |

## Swagger UI
- **경로**: /docs
- **OpenAPI spec**: /openapi.json
```

## 문서화 체크리스트

### Endpoint (api/routers/)
- [ ] 모든 endpoint에 `summary` (한국어)
- [ ] 모든 endpoint에 `description` (한국어)
- [ ] 에러 응답에 `responses` + 에러 코드
- [ ] Query/Path 파라미터에 `description`

### Schema (api/schemas/)
- [ ] 모든 스키마 클래스에 한 줄 docstring
- [ ] 모든 Field에 `description`
- [ ] 모든 Field에 `examples`
- [ ] 검증 규칙 명시 (`min_length`, `ge` 등)

### 최종 확인
- [ ] Swagger UI 렌더링 정상 확인 (`/docs`)
- [ ] 에러 코드 형식 일관성 (`E_[도메인]_[번호]`)
- [ ] 한국어 문서화 일관성

## 도구

```bash
# docstring 커버리지 측정
pip install interrogate
interrogate -v src/trend_korea/

# docstring 스타일 검증
pip install pydocstyle
pydocstyle --convention=google src/trend_korea/
```

## 커버리지 기준

| 대상 | 목표 |
|------|------|
| Endpoint summary/description | 100% |
| Pydantic Field description | 100% |
| Pydantic Field examples | 100% |
| 에러 응답 responses | 100% |
| Service/Repository docstring | 자명하지 않은 메서드만 |
