# Playgrounds

Playgrounds for supplementary materials of scientific articles, handy routines and chunks of code. There are at least three modalities to work with these playgrounds.

### Use the GitHub viewer

One, less powerful, consists in viewing a notebook using the integrated GitHub viewer. To do that, simply click on the notebook of interest and let GitHub do the rest.

### Clone and run using Miniconda

A second method gives full control on the notebooks and requires to clone the whole GitHub project, create a [Miniconda](https://docs.conda.io/en/latest/miniconda.html) environment with all the linked software dependencies, and finally to run the notebook stright on the local machine. This can be done as follows:

**Clone the notebook**

```
git clone https://github.com/mazzalab/playgrounds.git
cd playgrounds
```

**Create a new Miniconda environment and activate it**

Open a Miniconda command prompt, navigate to the _playgrounds_ folder where the project was cloned into and create the proper environment (e.g. environment_NAR_2021.yml),

```
conda env create -f environment_<<project>>.<<year>>.yml
conda activate playgrounds
```

**Open the notebook in the default browser**

```
jupyter notebook <<notebook_name>>.ipynb
```

### Use Binder or Colab

The easiest way to work with these notebooks is that of using third-party services that host notebooks and take care of any software requirements to make then running interactively in the browser as if they were installed locally. The only drawback of this method is that any change made on a notebook cannot be saved but will persist only until the end of the current session.

[Binder](https://mybinder.org/) and [Colab](https://colab.research.google.com/) links follow for each available notebook in this repository.

## HD Prevalence estimate 2014-2050

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/mazzalab/playgrounds/master?filepath=HD_prevalence_JNNP_2020.ipynb)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mazzalab/playgrounds/blob/master/HD_prevalence_JNNP_2020.ipynb)

## Gene co-expression networks (macroH2A1.1 and DDR)

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/mazzalab/playgrounds/master?filepath=macroH2A_IPS_StemCells_2021.ipynb)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mazzalab/playgrounds/blob/master/macroH2A_IPS_StemCells_2021.ipynb)

## Accumulated flow to tank nodes

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mazzalab/playgrounds/blob/master/accumulated_flow.ipynb)

## BEYOND COVID-19 PANDEMIC: TOPOLOGY-AWARE OPTIMIZATION OF VACCINATION STRATEGY FOR MINIMIZING VIRUS SPREADING

Here, we present the benefits of a topology-aware versus an age-based vaccination strategy to mitigate the spreading of the virus.
We provide a Jupyter notebook, that can be easily tested in GoogleColab. It carries out simulations with a fixed recovery rate of 14 days, with the possibility to modify both newtork topology and simulation parameters.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mazzalab/playgrounds/blob/master/Non_markov_SIR_covid.ipynb)

## APOGEE 2

A notebook to reproduce the whole APOGEE 2 learning protocol. It performs a two-stages analysis including the feature selection, MitImpact variants annotation, a nested cross-validation procedure, and performance measurement and comparison with other meta-predictors.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mazzalab/playgrounds/blob/master/apogee2_NMeth_2022.ipynb)

## HD Composite Cognition Score 
A notebook to calculate the Composite Cognition Score (CCS) starting from the following four UHDRS neuropsychological tests: Symbol Digit Modality Test (SDMT), Categorical Verbal Fluency Test (VFT), Stroop Color Reading Test (SCR), and Stroop Word Reading (SWR).

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/mazzalab/playgrounds/blob/master/CCS.ipynb)