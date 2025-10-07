# Oct 7 2025

1. Pelo que percebi, a ferramenta **Green Metrics Tool (GMT)** foi desenhada para avaliar aplicações utilizadas na indústria ([ref](https://docs.green-coding.io/docs/measuring/usage-scenario/)). A minha dúvida é a seguinte: caso venhamos a utilizar esta ferramenta, **devemos ter apenas um serviço/container que execute todo o benchmark**, ou é possível **dividir a medição por vários serviços/containers**? Para clarificar, quando falo em “benchmark” refiro-me a correr um **script `.sh` que executa vários programas e mede o seu consumo energético**, mas não tenho certeza se a ferramenta suporta este tipo de execução agregada. ([Exemplos que eles dão](https://docs.green-coding.io/docs/prologue/measurement-process/#:~:text=During%20the%20Runtime,etc.))

   - A:

2. O GMT oferece várias fases para o Measurement (Baseline, Installation, Boot, Idle, Runtime, Remove) [Measurement Plans](https://docs.green-coding.io/docs/prologue/measurement-phases/#:~:text=The%20Green%20Metrics%20Tool%20currently,Remove). Só vamos querer saber da **Runtime** ou devemos medir outras?

   - A:

