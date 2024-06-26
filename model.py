# pylint: skip-file
import os
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

# Enable following code for gpu mode only
# TORCH_GPU_DEVICE_ID = 0
# os.environ["CUDA_VISIBLE_DEVICES"] = f"{TORCH_GPU_DEVICE_ID}"

import time
import random
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM

import numpy as np

from instill.helpers.const import DataType, TextGenerationChatInput
from instill.helpers.ray_io import StandardTaskIO, serialize_byte_tensor
from instill.helpers.ray_config import instill_deployment, InstillDeployable
from instill.helpers import (
    construct_infer_response,
    construct_metadata_response,
    Metadata,
)


# from conversation import Conversation, conv_templates, SeparatorStyle

# torch.cuda.set_per_process_memory_fraction(
#     TORCH_GPU_MEMORY_FRACTION, 0  # it count of number of device instead of device index
# )


@instill_deployment
class Gemma2b:
    def __init__(self):
        print(f"torch version: {torch.__version__}")
        print(f"torch.cuda.is_available() : {torch.cuda.is_available()}")
        print(f"torch.cuda.device_count() : {torch.cuda.device_count()}")
        # print(f"torch.cuda.current_device() : {torch.cuda.current_device()}")
        # print(f"torch.cuda.device(0) : {torch.cuda.device(0)}")
        # print(f"torch.cuda.get_device_name(0) : {torch.cuda.get_device_name(0)}")

        # https://huggingface.co/google/gemma-2b
        # Download through huggingface

        ACCESS_TOKEN = "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"

        self.tokenizer = AutoTokenizer.from_pretrained(
            "google/gemma-2b", 
            torch_dtype=torch.float16, 
            low_cpu_mem_usage=True,
            token=ACCESS_TOKEN
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            "google/gemma-2b",
            device_map="cuda",
            torch_dtype=torch.float16,
            token=ACCESS_TOKEN
        )

        # Dyprecated: Predownload
        # self.tokenizer = AutoTokenizer.from_pretrained(
        #     model_path, torch_dtype=torch.float16, low_cpu_mem_usage=True
        #     )

        # self.model = AutoModelForCausalLM.from_pretrained(
        #     model_path,
        #     device_map="cuda",
        #     torch_dtype=torch.float16,
        # )

    def ModelMetadata(self, req):
        resp = construct_metadata_response(
            req=req,
            inputs=[
                Metadata(
                    name="prompt",
                    datatype=str(DataType.TYPE_STRING.name),
                    shape=[1],
                ),
                Metadata(
                    name="prompt_images",
                    datatype=str(DataType.TYPE_STRING.name),
                    shape=[1],
                ),
                Metadata(
                    name="chat_history",
                    datatype=str(DataType.TYPE_STRING.name),
                    shape=[1],
                ),
                Metadata(
                    name="system_message",
                    datatype=str(DataType.TYPE_STRING.name),
                    shape=[1],
                ),
                Metadata(
                    name="max_new_tokens",
                    datatype=str(DataType.TYPE_UINT32.name),
                    shape=[1],
                ),
                Metadata(
                    name="temperature",
                    datatype=str(DataType.TYPE_FP32.name),
                    shape=[1],
                ),
                Metadata(
                    name="top_k",
                    datatype=str(DataType.TYPE_UINT32.name),
                    shape=[1],
                ),
                Metadata(
                    name="random_seed",
                    datatype=str(DataType.TYPE_UINT64.name),
                    shape=[1],
                ),
                Metadata(
                    name="extra_params",
                    datatype=str(DataType.TYPE_STRING.name),
                    shape=[1],
                ),
            ],
            outputs=[
                Metadata(
                    name="text",
                    datatype=str(DataType.TYPE_STRING.name),
                    shape=[-1, -1],
                ),
            ],
        )
        return resp

    async def __call__(self, req):
        task_text_generation_chat_input: TextGenerationChatInput = (
            StandardTaskIO.parse_task_text_generation_chat_input(request=req)
        )
        print("----------------________")
        print(task_text_generation_chat_input)
        print("----------------________")

        print("print(task_text_generation_chat.prompt)")
        print(task_text_generation_chat_input.prompt)
        print("-------\n")

        print("print(task_text_generation_chat.prompt_images)")
        print(task_text_generation_chat_input.prompt_images)
        print("-------\n")

        print("print(task_text_generation_chat.chat_history)")
        print(task_text_generation_chat_input.chat_history)
        print("-------\n")

        print("print(task_text_generation_chat.system_message)")
        print(task_text_generation_chat_input.system_message)
        if len(task_text_generation_chat_input.system_message) is not None:
            if len(task_text_generation_chat_input.system_message) == 0:
                task_text_generation_chat_input.system_message = None
        print("-------\n")

        print("print(task_text_generation_chat.max_new_tokens)")
        print(task_text_generation_chat_input.max_new_tokens)
        print("-------\n")

        print("print(task_text_generation_chat.temperature)")
        print(task_text_generation_chat_input.temperature)
        print("-------\n")

        print("print(task_text_generation_chat.top_k)")
        print(task_text_generation_chat_input.top_k)
        print("-------\n")

        print("print(task_text_generation_chat.random_seed)")
        print(task_text_generation_chat_input.random_seed)
        print("-------\n")

        print("print(task_text_generation_chat.stop_words)")
        print(task_text_generation_chat_input.stop_words)
        print("-------\n")

        print("print(task_text_generation_chat.extra_params)")
        print(task_text_generation_chat_input.extra_params)
        print("-------\n")

        if task_text_generation_chat_input.temperature <= 0.0:
            task_text_generation_chat_input.temperature = 0.8

        if task_text_generation_chat_input.random_seed > 0:
            random.seed(task_text_generation_chat_input.random_seed)
            np.random.seed(task_text_generation_chat_input.random_seed)

        # No chat_history Needed
        # No system message Needed

        t0 = time.time()

        input_ids = self.tokenizer(
            task_text_generation_chat_input.prompt, 
            return_tensors="pt"
        ).to('cuda')
        
        sequences = self.model.generate(
            **input_ids,
            do_sample=True,
            top_k=task_text_generation_chat_input.top_k,
            temperature=task_text_generation_chat_input.temperature,
            max_new_tokens=task_text_generation_chat_input.max_new_tokens,
            **task_text_generation_chat_input.extra_params,
        )
        
        print(f"Inference time cost {time.time()-t0}s")

        max_output_len = 0

        text_outputs = []
        # for seq in sequences:
        #     print("Output No Clean ----")
        #     print(seq["generated_text"])
        #     # print("Output Clean ----")
        #     # print(seq["generated_text"][len(task_text_generation_chat_input.prompt) :])
        #     print("---")
        #     generated_text = seq["generated_text"].strip().encode("utf-8")
        #     text_outputs.append(generated_text)
        #     max_output_len = max(max_output_len, len(generated_text))

        seq = self.tokenizer.decode(sequences[0], skip_special_tokens=True)
        print("Output No Clean ----")
        print(seq)
        generated_text = seq[len(task_text_generation_chat_input.prompt) :].strip().encode("utf-8")
        print("Output Clean ----")
        print(generated_text)
        text_outputs.append(generated_text)
        max_output_len = max(max_output_len, len(generated_text))

        text_outputs_len = len(text_outputs)
        task_output = serialize_byte_tensor(np.asarray(text_outputs))
        # task_output = StandardTaskIO.parse_task_text_generation_output(sequences)

        print("Output:")
        print(task_output)
        print(type(task_output))

        return construct_infer_response(
            req=req,
            outputs=[
                Metadata(
                    name="text",
                    datatype=str(DataType.TYPE_STRING.name),
                    shape=[text_outputs_len, max_output_len],
                )
            ],
            raw_outputs=[task_output],
        )
        

entrypoint = (
    # https://github.com/instill-ai/python-sdk/blob/main/samples/tinyllama-gpu/model.py
    InstillDeployable(Gemma2b)
    .update_max_replicas(4)
    .update_min_replicas(1)
    .update_num_gpus(0.125) # 5G/40G
    .get_deployment_handle()
)
