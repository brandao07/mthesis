# Oct 7 2025

## [Green Metrics Tool](https://docs.green-coding.io/docs/prologue/introduction/)

It provides an estimate of your software’s energy consumption, allowing you to compare results over time and across different hardware setups to identify the most efficient system.

### Granularity

Green Metrics Tool support different levels of granularity:

- Machine wide (MCP, IPMI etc.) - low granularity
- Component wide (CPU, DRAM) - high granularity

Why care about the granularity level?

- To optimize software efficiently, sometimes you need detailed measurements (**high granularity**) so you know exactly which component is consuming the most energy and can target improvements.
- **Low granularity** is useful for quick comparisons between systems or for monitoring overall energy trends without needing fine detail.

### What does Green Metrics Tool provide?

While some tools ([Scaphandre](https://github.com/hubblo-org/scaphandre), [Kepler](https://github.com/sustainable-computing-io/kepler)) estimate energy per process or container, these are often approximate due to speculative execution and other factors. Green Metrics Tool takes a practical approach: it attributes the full machine energy to the software, providing consistent and realistic measurements. The cluster provided by GMT uses small, dedicated machines to reflect typical cloud VMs, with future support for separating components across machines.

### Containerization

The Green Metrics Tool is primarily designed to measure containerized applications and software [Docker](https://www.docker.com/).

**IMPORTANT:**

1. Some metrics are only measurable at the system level

   - For example, CPU energy or DRAM energy is usually measured for the whole machine, not for individual containers.
   - This is because the hardware reports total energy usage, not per-container usage.

2. Optional attribution to container level
   - Even though the measurement is for the whole system, the tool can **estimate** how much of that energy belongs to each container.

### Units & Dimensions

- GMT uses SI-Units for Bytes: 1kB = 1.000 Bytes instead of 1.024 Bytes.
- GMT stores values as 64-bit integers (**Smaller values are rounded.**):
  - Energy: min 1 µJ
  - Temp: min 0.01 °C
  - Utilization: min 0.01

# Oct 19 2025

## [Green Metrics Tool API](https://api.green-coding.io/docs)

### Submit Software

**POST** `https://api.green-coding.io/v1/software/add`

Example Payload

```json
{
  "name": "mthesis",
  "repo_url": "https://github.com/brandao07/mthesis",
  "email": "<email>",
  "filename": "./benchmarks/go/default.yml",
  "branch": "main",
  "machine_id": 5,
  "schedule_mode": "one-off"
}
```

Example Response

```json
{
  "success": true,
  "data": [59926]
}
```

### Get Phase Stats

**GET** `https://api.green-coding.io/v1/phase_stats/single/{run_id}`

Example Response

`mthesis/example-response.json`

## Other notes

I decided to run a separate container for each programming language to avoid creating an excessively large Docker image. I found that combining multiple compilers within a single image introduced unnecessary complexity and maintenance challenges.
