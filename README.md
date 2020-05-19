# BlockSim: Blockchain Simulator

A framework for modeling and simulate a Blockchain protocol.
It follows a discrete event simulation model. Currently, there are models to simulate **Bitcoin** and **Ethereum**.

This is an ongoing research project, these framework is in a **beta** stage.
If you find any issue, please report.

### Installation

We need to setup a Virtualenv and install all the dependencies

```sh
pip3 install virtualenv
virtualenv -p python3 venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### Running

```sh
python -m blocksim.main
```

## How to use and model

Check our wiki: https://github.com/BlockbirdLabs/blocksim/wiki

## Abstract

A blockchain is a distributed ledger in which participants that do not fully trust each other agree on the ledger's content by running a consensus algorithm.
This technology is raising a lot of interest both in academia and industry, but the lack of tools to evaluate design and implementation decisions may hamper fast progress. To address this issue, this paper presents a discrete-event simulator that is flexible enough to evaluate different blockchain implementations. These blockchains can be rapidly modeled and simulated by extending existing models.
Running Bitcoin and Ethereum simulations allowed us to change conditions and answer different questions about their performance. For example, we concluded that doubling the number of transactions per block has a low impact on the block propagation delay (10ms) and that encrypting communication has a high impact in that delay (more than 25%).

## Full paper

You can find the full paper here: https://www.carlosfaria.com/papers/blocksim-blockchain-simulator.pdf

Aditionaly, the presentation for the 2019 IEEE International Conference on Blockchain can be found here: https://www.carlosfaria.com/talks/blocksim-ieee-blockchain-2019.pdf
