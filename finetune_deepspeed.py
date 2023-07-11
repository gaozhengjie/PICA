# %%
import os
import sys
from typing import List

import fire
import torch
import transformers
from peft import (LoraConfig, TaskType, get_peft_model,
                  get_peft_model_state_dict, prepare_model_for_int8_training,
                  set_peft_model_state_dict)
from transformers import LlamaForCausalLM, LlamaTokenizer
from transformers.trainer_callback import TrainerControl, TrainerState
from transformers.trainer_utils import PREFIX_CHECKPOINT_DIR
from transformers.training_args import TrainingArguments

from datasets import load_dataset

class SavePeftModelCallback(transformers.TrainerCallback):
    def on_save(
        self, 
        args: TrainingArguments, 
        state: TrainerState, 
        control: TrainerControl, 
        **kwargs
    ):
        checkpoint_folder = os.path.join(args.output_dir, f"{PREFIX_CHECKPOINT_DIR} - {state.global_step}")
        kwargs["model"].save_pretrained(checkpoint_folder)
        pytorch_model_path = os.path.join(checkpoint_folder, "pytorch_model.bin")
        if os.path.exists(pytorch_model_path):
            os.remove(pytorch_model_path)
        return control
    
def train(
    # model/data params
    base_model: str = "",
    data_path: str = "dataset/train.jsonl",
    output_dir: str = "./checkpoints",
    # training hyperparams
    batch_size: int = 128,
    micro_batch_size: int = 16,
    num_epochs: int = 3,
    learning_rate: float = 3e-4,
    cutoff_len: int = 512,
    val_set_size: int = 2000,
    # lora hyperparams
    lora_r: int = 8,
    lora_alpha: int = 16,
    lora_dropout: float = 0.05,
    lora_target_modules: List[str] = [
        "q_proj",
        # "k_proj",
        "v_proj",
        # "down_proj",
        # "gate_proj",
        # "up_proj",
    ],
    add_eos_token: bool = False,
    group_by_length: bool = False,
    deepspeed: bool = True,
    # wandb params
    wandb_project: str = "",
    wandb_run_name: str = "",
    wandb_watch: str = "",
    wandb_log_model: str = "",
    resume_from_checkpoint: str = None,
):
    base_model = '/datas/huggingface/llama/{}'.format(base_model)
    if int(os.environ.get("LOCAL_RANK", 0)) == 0:
        print(
            f"Training Emo-LLM model with params:\n"
            f"base_model: {base_model}\n"
            f"data_path: {data_path}\n"
            f"output_dir: {output_dir}\n"
            f"batch_size: {batch_size}\n"
            f"micro_batch_size: {micro_batch_size}\n"
            f"num_epochs: {num_epochs}\n"
            f"learning_rate: {learning_rate}\n"
            f"cutoff_len: {cutoff_len}\n"
            f"val_set_size: {val_set_size}\n"
            f"lora_r: {lora_r}\n"
            f"lora_alpha: {lora_alpha}\n"
            f"lora_dropout: {lora_dropout}\n"
            f"lora_target_modules: {lora_target_modules}\n"
            f"add_eos_token: {add_eos_token}\n"
            f"group_by_length: {group_by_length}\n"
            f"deepspeed: {deepspeed}\n"
            f"wandb_project: {wandb_project}\n"
            f"wandb_run_name: {wandb_run_name}\n"
            f"wandb_watch: {wandb_watch}\n"
            f"wandb_log_model: {wandb_log_model}\n"
            f"resume_from_checkpoint: {resume_from_checkpoint or False}\n"
        )
        assert (
            base_model
        ), "Please specify a --base_model, e.g --base_model='huggyllama/llama-7b"

    gradient_accumulation_steps = batch_size // micro_batch_size
    device_map = "auto"
    world_size = int(os.environ.get("WORLD_SIZE", 1))
    ddp = world_size != 1
    if ddp:
        device_map = {"": int(os.environ.get("LOCAL_RANK") or 0)}
        gradient_accumulation_steps = gradient_accumulation_steps // world_size

    use_wandb = len(wandb_project) > 0 or (
        "WANDB_PROJECT" in os.environ and len(os.environ["WANDB_PROJECT"]) > 0
    )
    # only overwrite environ if wandb param passed
    if len(wandb_project) > 0:
        os.environ["WANDB_PROJECT"] = wandb_project
    if len(wandb_watch) > 0:
        os.environ["WANDB_WATCH"] = wandb_watch
    if len(wandb_log_model) > 0:
        os.environ["WANDB_LOG_MODEL"] = wandb_log_model

    # load model
    model = LlamaForCausalLM.from_pretrained(
        pretrained_model_name_or_path = base_model,
        load_in_8bit                  = False,
        device_map                    = device_map,
        torch_dtype                   = torch.float16,
    ).half()
    # model = prepare_model_for_int8_training(model)
    tokenizer = LlamaTokenizer.from_pretrained(
        pretrained_model_name_or_path = base_model,
        add_eos_token                 = True,
    )
    tokenizer.pad_token_id = 0
    tokenizer.eos_token_id = 2
    tokenizer.padding_side = "left"

    # peft
    peft_config = LoraConfig(
        task_type      = TaskType.CAUSAL_LM,
        inference_mode = False,
        r              = lora_r,
        lora_alpha     = lora_alpha,
        lora_dropout   = lora_dropout,
        target_modules = lora_target_modules,
        bias           = "none",
    )

    peft_config.save_pretrained(output_dir)

    model = get_peft_model(model, peft_config)

    if resume_from_checkpoint:
        checkpoint_name = os.path.join(
            resume_from_checkpoint, "pytorch_model.bin"
        )
        if not os.path.exists(checkpoint_name):
            checkpoint_name = os.path.join(
                resume_from_checkpoint, "adapter_model.bin"
            )
            resume_from_checkpoint = (
                False
            )
        if os.path.exists(checkpoint_name):
            print(f"Restarting from {checkpoint_name}")
            adapters_weights = torch.load(checkpoint_name, map_location="cuda")
            set_peft_model_state_dict(model, adapters_weights)
        else:
            print(f"Checkpoint {checkpoint_name} not found")

    model.print_trainable_parameters()

    def tokenize(example, add_eos_token=True):
        prompt = example['prompt']
        result = tokenizer(
            prompt,
            truncation     = True,
            max_length     = cutoff_len,
            padding        = False,
            return_tensors = None,
        )
        if (
            result["input_ids"][-1] != tokenizer.eos_token_id
            and len(result["input_ids"]) < cutoff_len
            and add_eos_token
        ):
            result["input_ids"].append(tokenizer.eos_token_id)
            result["attention_mask"].append(1)

        result["labels"] = result["input_ids"].copy()
        
        return result

    print("load dataset")


    dataset = load_dataset(
        'json',
        data_files = data_path,
        split      = 'train',
    )
    dataset = dataset.map(lambda x: tokenize(x), num_proc=8)
    # dataset = dataset.shuffle().select(range(10000))


    if val_set_size > 0:
        train_val = dataset.train_test_split(
            test_size = val_set_size, shuffle = True, seed = 42
        )
        train_data = (
            train_val["train"].shuffle()
        )
        val_data = (
            train_val["test"].shuffle()
        )
    else:
        train_data = dataset.shuffle()
        val_data = None

    print(train_data, val_data)

    if not ddp and torch.cuda.device_count() > 1:
        # keeps trainer from trying its own dp when more than 1 gpu is available
        model.is_parallelizable = True
        model.model_parallel = True

    # Training
    trainer = transformers.Trainer(
        model = model,
        train_dataset = train_data,
        eval_dataset = val_data,
        args = transformers.TrainingArguments(
            per_device_train_batch_size = micro_batch_size,
            gradient_accumulation_steps = gradient_accumulation_steps,
            # warmup_steps                = 100,
            warmup_ratio                = 0.1,
            num_train_epochs            = num_epochs,
            learning_rate               = learning_rate,
            fp16                        = True,
            logging_steps               = 10,
            evaluation_strategy         = "steps" if val_set_size > 0 else "no", 
            save_strategy               = 'steps',
            eval_steps                  = 40 if val_set_size > 0 else None,
            save_steps                  = 40,
            output_dir                  = output_dir,
            save_total_limit            = 20,
            load_best_model_at_end      = True if val_set_size > 0 else False,
            ddp_find_unused_parameters  = False if ddp else None,
            optim                       = "adamw_torch",
            group_by_length             = group_by_length,
            report_to                   = "wandb" if use_wandb else None,
            run_name                    = wandb_run_name if use_wandb else None,
            deepspeed                   = "deepspeed-config.json" if deepspeed else None
        ),
        data_collator = transformers.DataCollatorForSeq2Seq(
            tokenizer          = tokenizer,
            pad_to_multiple_of = 8,
            return_tensors     = "pt",
            padding            = True
        ),
        # callbacks     = [SavePeftModelCallback],
    )
    model.config_use_cache = False

    old_state_dict = model.state_dict
    model.state_dict = (
        lambda self, *_, **__: get_peft_model_state_dict(self, old_state_dict())
    ).__get__(model, type(model))

    if torch.__version__ >= "2" and sys.platform != "win32":
        model = torch.compile(model)

    trainer.train(resume_from_checkpoint=resume_from_checkpoint)

    print(
        "\n If there's a warning about missing keys above, please disregard :)"
    )

    model.save_pretrained(output_dir)

if __name__ == "__main__":
    fire.Fire(train)