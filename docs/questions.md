# Oct 7 2025

1. Pelo que percebi, a ferramenta **Green Metrics Tool (GMT)** foi desenhada para avaliar aplicações utilizadas na indústria ([ref](https://docs.green-coding.io/docs/measuring/usage-scenario/)). A minha dúvida é a seguinte: caso venhamos a utilizar esta ferramenta, **devemos ter apenas um serviço/container que execute todo o benchmark**, ou é possível **dividir a medição por vários serviços/containers**? Para clarificar, quando falo em “benchmark” refiro-me a correr um **script `.sh` que executa vários programas e mede o seu consumo energético**, mas não tenho certeza se a ferramenta suporta este tipo de execução agregada. ([Exemplos que eles dão](https://docs.green-coding.io/docs/prologue/measurement-process/#:~:text=During%20the%20Runtime,etc.))

   - A: Só um container. (Simão)

2. O GMT oferece várias fases para o Measurement (Baseline, Installation, Boot, Idle, Runtime, Remove) [Measurement Plans](https://docs.green-coding.io/docs/prologue/measurement-phases/#:~:text=The%20Green%20Metrics%20Tool%20currently,Remove). Só vamos querer saber da **Runtime** ou devemos medir outras?

   - A: Runtime. (Simão)

# Oct 8 2025

3. Consegui por o GMT a funcionar só que por algum motivo muitas das métricas não foram retiradas (ex: consumo de energia, DRAM). Eles referem na documentação que a versão para o macOS está bastante limitada e só é recomendada para testes [ref](https://docs.green-coding.io/docs/installation/installation-macos/#:~:text=Running%20the%20GMT%20on%20Macs%20will%20never%20give%20you%20correct%20measurements!%20It%20should%20only%20ever%20be%20used%20to%20test%20your%20project%20for%20correctness%20in%20that%20it%20will%20run%20on%20the%20GMT%20but%20never%20to%20benchmark%20software). O que seria melhor fazer?

**Update:** Testei na máquina deles e as métricas estão a ser todas retiradas [Exemplo](https://metrics.green-coding.io/stats.html?id=0d643526-d741-4be4-94d5-f936b4f4f923).

- A:

# Oct 12 2025

4. Para obter os resultados, é necessário executar o ficheiro `usage_scenario.yml`. Teríamos de o executar **x** vezes, uma vez que este ficheiro contém todos os benchmarks. Gostaria de saber a vossa opinião sobre esta abordagem. **(DEPRECATED)**

   - A: Em relação à pergunta `4.`, encontrei esta informação [ref](https://docs.green-coding.io/docs/measuring/comparing-measurements/#:~:text=in%20all%20runs.-,Comparing%20repeated%20runs,-%23), pelo que percebi pelo GUI deles dá para configurar quantas runs é que quero executar e depois compilar. (André)

# Oct 16 2025

5. Na reunião de quarta-feira 15 Oct 2025, surgiu uma dúvida sobre como obter os dados do **Green Metrics Tool**, uma vez que o acesso atual é apenas visual através do website, o que torna a extração dos valores pouco prática.

Durante a pesquisa, encontrei a seguinte documentação que pode ajudar:  
[Export Formats — Green Metrics Tool](https://docs.green-coding.io/docs/declarations/export-formats/#:~:text=Export%20formats,-Green%20Metrics%20Tool)

No entanto, a documentação da API é um pouco vaga. Gostava de contar com algum apoio do lado da **empresa responsável pela ferramenta**, se possível. **(DEPRECATED)**

**Update:** Descobri o endpoint que queremos (ACHO EU), `https://api.green-coding.io/v1/phase_stats/single/<run-uuid>` é preciso confirmar.

- A:

# Oct 18 2025

6. Configurei os _benchmarks_ do CLBG em Go com a Green Metrics Tool e identifiquei os seguintes problemas: devido ao tamanho elevado do _output_ gerado pelos programas **fasta** e **mandelbrot**, o GMT acaba por falhar ao tentar guardar os registos (_logs_), uma vez que excede o limite do _buffer_. Encontrei uma solução sugerida pela própria ferramenta, através da opção `log-stdout` ([referência](<https://docs.green-coding.io/docs/measuring/usage-scenario/#:~:text=in%20your%20container-,log%2Dstdout%3A%20%5Bboolean%5D%20(optional%2C%20default%3A%20true),and%20make%20it%20available%20through%20the%20frontend%20in%20the%20Logs%20tab.,-Please%20see%20the>)).

Além disso, a documentação recomenda que, sempre que o volume de _logs_ for excessivo, estes devem ser desativados, de forma a evitar sobrecarga e erros de execução ([_Best Practices_](https://docs.green-coding.io/docs/measuring/best-practices/#:~:text=However%2C%20you%20should%20consider%20turning%20logging%20off%20when%20there%20is%20extensive%20logging%20output%2C%20as%20it%20can%20create%20overhead.)).

No entanto, permanece a dúvida sobre se desativar os _logs_ desta forma poderá afetar o desempenho dos _benchmarks_ que avaliam operações de entrada/saída (_I/O_), uma vez que esses resultados são relevantes para a análise global de desempenho.

- A:

# Oct 19 2025

7.  Estou a pensar criar um programa que tenha duas funcionalidades:

    1.  Aceita um array de requests e submete na API da GMT.

        Exemplo:

        ```json
        {
          "name": "My Benchmark",
          "repo_url": "https://github.com/brandao07/mthesis",
          "email": "andrebrandleao@hotmail.com",
          "branch": "main",
          "machine_id": 5,
          "schedule_mode": "one-off",
          "benchmarks": [
            {
              "name": "Go",
              "filename": "./benchmarks/go/default.yml"
            },
            {
              "name": "NodeJS",
              "filename": "./benchmarks/nodejs/default.yml"
            }
          ]
        }
        ```

    2.  O programa recebe um array de UUIDs de execuções e, para cada um, faz uma requisição ao endpoint `https://api.green-coding.io/v1/phase_stats/single/{run_id}`. Em seguida, extrai os dados relevantes das respostas JSON e converte-os num ficheiro CSV legível, onde cada linha representa uma execução (um UUID) e contém as principais métricas obtidas do endpoint.

Gostava de saber a vossa opinião.

A:
