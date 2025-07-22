---
language:
- ru
---
# T-lite-it-1.0

**🚨 T-lite is designed for further fine-tuning and is not intended as a ready-to-use conversational assistant. Users are advised to exercise caution and are responsible for any additional training and oversight required to ensure the model's responses meet acceptable ethical and safety standards. The responsibility for incorporating this model into industrial or commercial solutions lies entirely with those who choose to deploy it.**


## Description

T-lite-it-1.0 is a model built upon the Qwen 2.5 model family and incorporates both continual pre-training and alignment techniques.

### 📚 Dataset

Pre-training Stage 1:
100B tokens, consisting of diverse Russian data from Common Crawl, books, code, and proprietary datasets, mixed with re-played English data (English added as it is the primary language of the base model).

Pre-training Stage 2:
40B tokens, a mix of instruction and pre-training data.

Supervised Fine-Tuning (SFT):
1B tokens, a mix of diverse instruction data.

Preference Tuning:
1B tokens, training the model to be helpful.

## 📊 Benchmarks

| Benchmark                                      | T-lite-it-1.0 | Qwen-2.5-7B-Instruct | GigaChat Pro 1.0.26.15 | RuAdapt-Qwen-7B-Instruct-v1 | gemma-2-9b-it | 
|------------------------------------------------|:-------------:|:--------------------:|:----------------------:|:---------------------------:|:--------------|
| [MERA](https://mera.a-ai.ru)                   |   **0.552**   |        0.482         |         0.512          |            0.468            |  0.505 |
| [MaMuRaMu](https://mera.a-ai.ru/ru/tasks/22)   |   **0.775**   |        0.711         |          0.77          |             0.7             | 0.724  |
| ruMMLU-PRO                                     |     **0.497**     |        0.481         |           -            |            0.448            |  0.405 |
| ruGSM8K                                        |     **0.856**     |        0.832         |         0.752          |            0.795            |  0.823 |
| ruMATH                                         |     **0.679**     |        0.671         |         0.418          |            0.607            |  0.473 |
 | ruMBPP                                         |     **0.693**     |       0.685         |         0.412          |            0.696            |  0.63 |
 | [ruCodeEval](https://mera.a-ai.ru/ru/tasks/23) | 0.082 / 0.168 / 0.226 | 0.025 / 0.071 / 0.098 | 0.056 / 0.068 / 0.073 |    0.018 / 0.064 / 0.11     | **0.215 / 0.494 / 0.561** |
| Arena-Hard-Ru                                  | **64.38** | 54.29 | - |            52.77            | 47.83 | 
| MT Bench Ru                                    | 7.87 | 7.33 | **8.21** |            7.62             | 7.4 |
 | Alpaca Eval Ru                                 | **39.61** | 25.61 | 29.83 |            28.43            | 36.87 |

Detailed evaluation results can be found in our [habr post](https://habr.com/ru/companies/tbank/articles/865582/)


## 👨‍💻 Examples of usage

### HF Usage

```python
from transformers import AutoTokenizer, AutoModelForCausalLM
import torch
torch.manual_seed(42)

model_name = "t-tech/T-lite-it-1.0"
tokenizer = AutoTokenizer.from_pretrained(model_name)
model = AutoModelForCausalLM.from_pretrained(
    model_name, 
    torch_dtype="auto",
    device_map="auto"
)

prompt = "Напиши стих про машинное обучение"
messages = [
    {"role": "system", "content": "Ты T-lite, виртуальный ассистент в Т-Технологии. Твоя задача - быть полезным диалоговым ассистентом."},
    {"role": "user", "content": prompt}
]
text = tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=True
)
model_inputs = tokenizer([text], return_tensors="pt").to(model.device)

generated_ids = model.generate(
    **model_inputs,
    max_new_tokens=256
)
generated_ids = [
    output_ids[len(input_ids):] for input_ids, output_ids in zip(model_inputs.input_ids, generated_ids)
]

response = tokenizer.batch_decode(generated_ids, skip_special_tokens=True)[0]

print(response)
```

Output:
```
В мире данных, где цифры танцуют,  
Машинное обученье — ведущий вальс.  
Алгоритмы учатся, как дети,  
На примерах, как на сказочных страницах.

Они ищут закономерности в потоках,  
Как мудрецы в древних свитках.  
С каждым шагом всё точнее предсказания,  
Вот так, словно волшебство, оживает.

Обучаясь на ошибках, они растут,  
Из простых моделей в сложные формы.  
Каждый новый пример — как новая строка,  
В книге знаний, что не знает конца.

Не бойтесь перемен, ведь это — путь,  
Который ведёт к будущему, светлому и новому.  
Машинное обученье — наш проводник,  
В этом мире, где технологии царят.
```

### VLLM Usage

```python
from transformers import AutoTokenizer
from vllm import LLM, SamplingParams

model_name = "t-tech/T-lite-it-1.0"
tokenizer = AutoTokenizer.from_pretrained(model_name)
llm = LLM(model=model_name, max_model_len=8192)
sampling_params = SamplingParams(temperature=0.7,
                                repetition_penalty=1.05,
                                top_p=0.8, top_k=70)

prompt = "Напиши стих про машинное обучение"
messages = [
    {"role": "system", "content": "Ты T-lite, виртуальный ассистент в Т-Технологии. Твоя задача - быть полезным диалоговым ассистентом."},
    {"role": "user", "content": prompt}
]

prompt_token_ids = tokenizer.apply_chat_template(messages, add_generation_prompt=True)

outputs = llm.generate(prompt_token_ids=prompt_token_ids, sampling_params=sampling_params)

generated_text = [output.outputs[0].text for output in outputs]
print(generated_text)
```