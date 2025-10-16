# Oct 7 2025

1. Pelo que percebi, a ferramenta **Green Metrics Tool (GMT)** foi desenhada para avaliar aplicações utilizadas na indústria ([ref](https://docs.green-coding.io/docs/measuring/usage-scenario/)). A minha dúvida é a seguinte: caso venhamos a utilizar esta ferramenta, **devemos ter apenas um serviço/container que execute todo o benchmark**, ou é possível **dividir a medição por vários serviços/containers**? Para clarificar, quando falo em “benchmark” refiro-me a correr um **script `.sh` que executa vários programas e mede o seu consumo energético**, mas não tenho certeza se a ferramenta suporta este tipo de execução agregada. ([Exemplos que eles dão](https://docs.green-coding.io/docs/prologue/measurement-process/#:~:text=During%20the%20Runtime,etc.))

   - A: Só um container. (Simão)

2. O GMT oferece várias fases para o Measurement (Baseline, Installation, Boot, Idle, Runtime, Remove) [Measurement Plans](https://docs.green-coding.io/docs/prologue/measurement-phases/#:~:text=The%20Green%20Metrics%20Tool%20currently,Remove). Só vamos querer saber da **Runtime** ou devemos medir outras?

   - A: Runtime. (Simão)

# Oct 8 2025

3. Consegui por o GMT a funcionar só que por algum motivo muitas das métricas não foram retiradas (ex: consumo de energia, DRAM). Eles referem na documentação que a versão para o macOS está bastante limitada e só é recomendada para testes [ref](https://docs.green-coding.io/docs/installation/installation-macos/#:~:text=Running%20the%20GMT%20on%20Macs%20will%20never%20give%20you%20correct%20measurements!%20It%20should%20only%20ever%20be%20used%20to%20test%20your%20project%20for%20correctness%20in%20that%20it%20will%20run%20on%20the%20GMT%20but%20never%20to%20benchmark%20software). O que seria melhor fazer?

   - A: 

# Oct 12 2025

4. Para obter os resultados, é necessário executar o ficheiro `usage_scenario.yml`. Teríamos de o executar **x** vezes, uma vez que este ficheiro contém todos os benchmarks. Gostaria de saber a vossa opinião sobre esta abordagem. **(DEPRECATED)**

   - A: Em relação à pergunta `4.`, encontrei esta informação [ref](https://docs.green-coding.io/docs/measuring/comparing-measurements/#:~:text=in%20all%20runs.-,Comparing%20repeated%20runs,-%23), pelo que percebi pelo GUI deles dá para configurar quantas runs é que quero executar e depois compilar. (André)

# Oct 16 2025

5. Na reunião de quarta-feira 15 Oct 2025, surgiu uma dúvida sobre como obter os dados do **Green Metrics Tool**, uma vez que o acesso atual é apenas visual através do website, o que torna a extração dos valores pouco prática.

Durante a pesquisa, encontrei a seguinte documentação que pode ajudar:  
[Export Formats — Green Metrics Tool](https://docs.green-coding.io/docs/declarations/export-formats/#:~:text=Export%20formats,-Green%20Metrics%20Tool)

No entanto, a documentação da API é um pouco vaga. Gostava de contar com algum apoio do lado da **empresa responsável pela ferramenta**, se possível.

   - A:
