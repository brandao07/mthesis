# Oct 7 2025

1. Pelo que percebi, a ferramenta **Green Metrics Tool (GMT)** foi desenhada para avaliar aplicações utilizadas na indústria ([ref](https://docs.green-coding.io/docs/measuring/usage-scenario/)). A minha dúvida é a seguinte: caso venhamos a utilizar esta ferramenta, **devemos ter apenas um serviço/container que execute todo o benchmark**, ou é possível **dividir a medição por vários serviços/containers**? Para clarificar, quando falo em “benchmark” refiro-me a correr um **script `.sh` que executa vários programas e mede o seu consumo energético**, mas não tenho certeza se a ferramenta suporta este tipo de execução agregada. ([Exemplos que eles dão](https://docs.green-coding.io/docs/prologue/measurement-process/#:~:text=During%20the%20Runtime,etc.))

   - A:

2. O GMT oferece várias fases para o Measurement (Baseline, Installation, Boot, Idle, Runtime, Remove) [Measurement Plans](https://docs.green-coding.io/docs/prologue/measurement-phases/#:~:text=The%20Green%20Metrics%20Tool%20currently,Remove). Só vamos querer saber da **Runtime** ou devemos medir outras?

   - A:

# Oct 8 2025

3. Consegui por o GMT a funcionar só que por algum motivo muitas das métricas não foram retiradas (ex: consumo de energia, DRAM). Eles referem na documentação que a versão para o macOS está bastante limitada e só é recomendada para testes [ref](https://docs.green-coding.io/docs/installation/installation-macos/#:~:text=Running%20the%20GMT%20on%20Macs%20will%20never%20give%20you%20correct%20measurements!%20It%20should%20only%20ever%20be%20used%20to%20test%20your%20project%20for%20correctness%20in%20that%20it%20will%20run%20on%20the%20GMT%20but%20never%20to%20benchmark%20software). O que seria melhor fazer?

   - A:
