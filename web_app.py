"""网页程序的主入口点"""
import hydra
import logging
import rootutils
from omegaconf import DictConfig, OmegaConf



rootutils.setup_root(__file__, indicator=".project-root", pythonpath=True)
# ------------------------------------------------------------------------------------ #
# the setup_root above is equivalent to:
# - adding project root dir to PYTHONPATH
#       (so you don't need to force user to install project as a package)
#       (necessary before importing any local modules e.g. `from src import utils`)
# - setting up PROJECT_ROOT environment variable
#       (which is used as a base for paths in "configs/paths/default.yaml")
#       (this way all filepaths are the same no matter where you run the code)
# - loading environment variables from ".env" in root dir
#
# you can remove it if you:
# 1. either install project as a package or move entry files to project root dir
# 2. set `root_dir` to "." in "configs/paths/default.yaml"
#
# more info: https://github.com/ashleve/rootutils
# ------------------------------------------------------------------------------------ #

from src.dialogue_agent.agent import DialogueAgent
from src.webui.gradio_demo import run_gradio


log = logging.getLogger(__name__)


def agent_init(cfg: DictConfig) -> DialogueAgent:
    """
    Initialize DialogueAgent
    """
    # backbone_bot
    log.info(f"Initializing backbone_bot <{cfg.backbone_bot._target_}>")
    backbone_bot = hydra.utils.instantiate(cfg.backbone_bot)
    # agent
    log.info(f"Initializing DialogueAgent <{cfg.dialogue_system._target_}>")
    agent = hydra.utils.instantiate(
        cfg.dialogue_system,
        llm=backbone_bot,
        _recursive_=False
    )
    return agent


@hydra.main(version_base="1.3", config_path="configs", config_name="web_app")
def main(cfg: DictConfig) -> None:
    """
    Main function
    """
    print(OmegaConf.to_yaml(cfg))
    
    agent = agent_init(cfg)
    
    log.info("Running web app")
    run_gradio(agent)
    
    
if __name__ == "__main__":
    main()