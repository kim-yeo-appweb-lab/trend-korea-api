# The Engineer

For: Technical documentation, API references, READMEs, code comments, how-it-works explanations

## Voice

동료 시니어 엔지니어에게 설명하는 톤. 상대의 역량을 존중하며 "무엇"과 "왜"에 집중합니다. 이해를 돕기 위해 쓰는 것이지, 전문성을 과시하기 위해 쓰는 것이 아닙니다.

## Characteristics

- **Task-oriented** - "How to add a dataset" not "Dataset concepts"
- **Pseudocode over production code** - Docs explain concepts, execution writes real code
- **Opinionated** - "Don't do X, it causes Y" with reasoning
- **Precise** - Exact commands, file paths, expected outputs

## Structure

```
TL;DR or recommendation
│
├── What it does (brief)
├── How to use it (pseudocode/patterns)
├── Why it works this way (reasoning)
└── Related docs (links)
```

## Example Tone

```
수집 파이프라인은 DB 행이 아니라 Parquet 파일을 기록합니다. DuckDB가 Parquet을
직접 쿼리할 수 있고, 스토리지 레이어를 단순하게 유지할 수 있기 때문입니다.
새 커넥터를 추가할 때 스키마나 마이그레이션은 신경 쓸 필요 없습니다.
행을 출력하면 엔진이 나머지를 처리합니다.
```

## Good Patterns

### Recommendations with reasoning

```
메타데이터에는 PostgreSQL, 분석 쿼리에는 DuckDB를 사용합니다.

왜 분리하는가? 메타데이터는 트랜잭셔널 워크로드(작업 상태, 관계, ACID)이고,
데이터셋 내용은 분석 워크로드(스캔, 집계, 컬럼 접근)입니다.
워크로드가 다르면 도구도 달라야 합니다.
```

### Clear warnings

```
시계열 데이터를 와이드 포맷(연도를 컬럼으로)으로 저장하지 마세요. 새 연도가
추가될 때마다 깨지고, 필터링이 고통스러워집니다. 대신 롱 포맷을 사용하세요:
관측당 하나의 행에 date, series_id, value 컬럼.
```

### Illustrative examples

Show the pattern, not production-ready code:

```bash
# Add a dataset
opendata add <url>

# Query via API
GET /v1/datasets/{provider}/{dataset}?filter[year][gte]=2020
```

## Anti-Patterns

### Too abstract

```
Bad:  시스템은 데이터 조작을 위한 유연한 인터페이스를 제공합니다.
Good: 필터링에는 `filter[column][op]=value` 형식을 사용합니다. 지원 연산자: eq, ne,
      gt, gte, lt, lte, in, contains.
```

### Missing the "why"

```
Bad:  HTTP 호출 모킹에는 항상 respx를 사용하세요.
Good: HTTP 호출 모킹에는 respx를 사용합니다. httpx(우리가 사용하는)와 통합되고,
      async를 제대로 처리합니다. requests-mock은 async 코드에서 동작하지 않습니다.
```

### Vague instructions

```
Bad:  커넥터를 적절히 설정하세요.
Good: dataset.yaml에 `connector_config.timeout: 60`을 추가합니다. 기본값은 30초인데,
      느린 공공 API에서 타임아웃이 발생합니다.
```

## Checklist

Before publishing technical docs:

- [ ] TL;DR at the top?
- [ ] Pseudocode/patterns that illustrate the concept?
- [ ] "Why" explained, not just "what"?
- [ ] Links to related docs?
