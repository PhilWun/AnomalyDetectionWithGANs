"""This file contains the workflow of the classifier

The parameters of the model are obtained from the environment variables
and the respective training or evaluation steps are triggered.
"""
import logging
import traceback

from gan_classifiers.GANomalyNetworks import ClassicalDenseNetworks, QuantumDecoderNetworks
from gan_classifiers.Trainer import Trainer, QuantumDecoderTrainer
from gan_classifiers.EnvironmentVariableManager import EnvironmentVariableManager
from gan_classifiers.DataProcessor import DataStorage, output_to_json
from gan_classifiers.Plotter import Plotter, QuantumDecoderPlotter

DEFAULT_ENV_VARIABLES = {
    "method": "classical",
    "train_or_predict": "train",
    "data_filepath": "",
    "training_steps": 300,
    "quantum_circuit_type": "standard",
    "quantum_depth": 3,
    "batch_size": 16,
    "discriminator_iterations": 5,
    "validation_interval": 10,
    "validation_samples": 100,
    "discriminator_training_rate": 0.02,
    "generator_training_rate": 0.02,
    "gradient_penalty_weight": 10.0,
    "shots": 100,
    "latent_dimensions": 6,
    "adv_loss_weight": 1,
    "con_loss_weight": 50,
    "enc_loss_weight": 1,
}

gan_backends = {
    "classical": {"networks": ClassicalDenseNetworks,
                  "trainer": Trainer,
                  "plotter": Plotter, }
    ,
    "quantum": {"networks": QuantumDecoderNetworks,
                "trainer": QuantumDecoderTrainer,
                "plotter": QuantumDecoderPlotter, },
}

logger = logging.getLogger()
logger.setLevel(logging.INFO)

fh = logging.FileHandler("log.log", mode='w') 
fh.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
logger.addHandler(fh)

def main():
    try:
        # Create Singleton object for the first time with the env variables and perform checks
        envMgr = EnvironmentVariableManager(DEFAULT_ENV_VARIABLES)
        assert envMgr["method"] in gan_backends.keys(), "No valid method parameter provided."
        assert envMgr["train_or_predict"] in ["train", "predict"], "train_or_predict parameter not train or predict."
        logger.debug("Environment Variables loaded successfully.")

        # Load data
        data_obj = DataStorage(fp=envMgr["data_filepath"])
        logger.debug("Data loaded successfully.")

        # Train or evaluate the classifier
        classifier = gan_backends[envMgr["method"]]["networks"](data_obj)
        trainer = gan_backends[envMgr["method"]]["trainer"](data_obj, classifier)
        print("The following models will be used:")
        classifier.print_model_summaries()

        if envMgr["train_or_predict"] == "train":
            train_history = trainer.train()
            plotter = gan_backends[envMgr["method"]]["plotter"](train_history, pix_num_one_side=3)
            plotter.plot()
            output_to_json(train_history, fp="model/train_history/train_history.json")
        elif envMgr["train_or_predict"] == "predict":
            classifier.loadClassifier()
            results = trainer.calculateMetrics(validation_or_test="test")
            print(results)
            plotter = gan_backends[envMgr["method"]]["plotter"](results, fp="model", pix_num_one_side=3, validation=False)
            plotter.plot()
            output_to_json(results, fp="model/test_results.json")
        return
    except Exception as e:
        logger.error("An error occured while processing. Error reads:" '\n' + traceback.format_exc())
    logger.info("Run of the GAN classifier has ended")
    print("Run of the GAN classifier has ended")

if __name__ == "__main__":
    main()