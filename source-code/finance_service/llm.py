# finance_service/llm.py

import torch
from transformers import AutoTokenizer, AutoModelForCausalLM


class LocalLlamaLLM:
    def __init__(
        self,
        model_name="TinyLlama/TinyLlama-1.1B-Chat-v1.0",
        device=None,
    ):
        if device:
            self.device = device
        elif torch.backends.mps.is_available():
            self.device = "mps"
        elif torch.cuda.is_available():
            self.device = "cuda"
        else:
            self.device = "cpu"

        print(f"[LLM] Using device: {self.device}")

        dtype = torch.float16 if self.device in ("cuda", "mps") else torch.bfloat16

        self.tokenizer = AutoTokenizer.from_pretrained(model_name)

        # TinyLlama has no pad token by default; set it to avoid MPS crashes
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token

        self.model = AutoModelForCausalLM.from_pretrained(
            model_name,
            torch_dtype=dtype,
        ).to(self.device)

        # Mirror pad_token_id on the model config
        self.model.config.pad_token_id = self.tokenizer.pad_token_id

        self.model.eval()

    def generate(self, prompt: str, max_tokens: int = 60, **kwargs) -> str:
        inputs = self.tokenizer(
            prompt,
            return_tensors="pt",
            padding=True,
        ).to(self.device)

        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                do_sample=False,
                num_beams=1,
                use_cache=True,
                # Pass eos explicitly to avoid torch.isin at runtime on MPS
                eos_token_id=self.tokenizer.eos_token_id,
                pad_token_id=self.tokenizer.pad_token_id,
            )

        result = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        return result[len(prompt):].strip()
