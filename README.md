# Evo tree detection
This repository contains the code for creating a new Evo tree map, which includes dead trees as a new species class. A summary of how the tree map was created is presented below. The majority of the processing steps have been replicated from [Mäyrä et al. (2021)](https://doi.org/10.1016/j.rse.2021.112322) and the corresponding [GitHub repository](https://github.com/mayrajeo/tree-detection-evo).

## Datasets
- **Hyperspectral aerial images** with a resolution of 0.5 m for VNIR channels and 1 m for SWIR channels
-  **Airborne LiDAR data** with a point density of 10.2 p/m<sup>2<sup>
- **Ground reference data**
 
More details about the datasets can be found from sections 2.2 and 2.3 in  Mäyrä et al. (2021) and the related GitHub repository. The only difference to the datasets presented in Mäyrä et al. (2021) were the additional 243 standing dead tree observations added to the ground reference data. Some of these were dead tree observations measured in the field, whereas others were dead tree observations digitized from aerial images. Anton Kuzmin from UEF provided the deadwood data and he can probably provide more details regarding the collection of the dead tree data.

## Methodology
In summary, the methodology consisted of the following steps:
1. Preprocessing
2. Delineating individual tree segments
3. Computing features for the segments
4. Matching airborne data with ground reference data
5. Training and validating tree species classifiers
6. Creating a wall-to-wall tree map

### Preprocessing
The preprocessing steps were exactly the same as in section 2.2 in Mäyrä et al. (2021), except the interpolated hyperspectral bands were not discarded.

### Delineating individual tree segments
Individual tree segments were delineated from the LiDAR dataset using a canopy height model (CHM) based algorithm available in the [lidR package](https://cran.r-project.org/web/packages/lidR/index.html). First, treetops were searched from the CHM using lidR's lmf algorithm, which is based on [Popescu and Wynne (2004)](https://doi.org/10.14358/PERS.70.5.589). The algorithm searches for treetops as local maxima within a moving window of a specified size. A window size of 5 m and a minimum tree height of 10 m were used as input parameters for the algorithm. After detecting treetops, crowns were delineated around these treetops using lidR's dalponte2016 region growing algorithm, which is based on [Dalponte and Coomes (2016)](https://doi.org/10.1111/2041-210X.12575). The parameters used for the algorithm were th_tree = 10 m, th_seed = 0.65, th_cr = 0.5, and max_cr = 5. 

### Computing features for the segments
The hyperspectral data were matched with the delineated tree segments to enable computing spectral features for each tree segment. Each tree segment was matched with all hyperspectral pixels whose center was located within the bounds of the segment crown polygon. The band-specific mean, minimum, maximum, standard deviation, kurtosis, and skewness of these hyperspectral pixels were then computed to be used as the features. The hyperspectral data consisted of 460 spectral bands plus a band representing the CHM. Thus, the total number of computed features was (460+1)*6 = 2766.  

### Matching airborne data with ground reference data
The tree segments were matched with ground reference data to extract training and test data for tree species classifiers. Only reference trees with a diameter at breast height over 150 mm were considered for matching. The matching process was the following:
```
for each tree segment:
	Find all reference trees located within the crown polygon.
	if no trees within the crown polygon:
		Do not match the segment with a reference tree.
	else if one tree within the crown polygon:
		Match the segment with the reference tree.
	else:
		Match the segment with the reference tree closest to the
		treetop.
```
The hyperspectral data were tiled into 21 rows and 23 columns. The matched trees located within four of these columns were left as test data, whereas the rest were used as training data. The table below shows the species-specific numbers of observations in the training and test datasets.

|| Train | Test |	 
|----|--|--|
| Birch | 378 | 47 |
| Deadwood | 44 | 12 |
| European aspen | 294 | 69 |
| Norway spruce | 520 | 66 |
| Scots pine | 723| 111 |
| Total | 1959 | 305 |

### Training and validating tree species classifiers
Various machine learning models were trained for classifying the tree segments into different species. Among the tested models were k-nearest neighbors (KNN), logistic regression, random forest (RF), the support vector machine (SVM; with a linear and RBF kernel), the gradient boosting machine (GBM), and the multilayer perceptron (MLP). KNN, RF, and SVM were implemented with [scikit-learn](https://scikit-learn.org/stable/), the GBM with [LightGBM](https://lightgbm.readthedocs.io/en/stable/), and the MLP with [fastai](https://docs.fast.ai/) , which provides a higher level interface for [PyTorch](https://pytorch.org/).

Based on the performance on a separate validation dataset, the MLP was selected as the final tree species classifier. The MLP consisted of two hidden layers with rectified linear unit (ReLU) activation and batch normalization. The first hidden layer had 200 neurons, whereas the second had 100 neurons. Deadwood instances were given a higher weight during training to counter the class imbalance in the dataset. 

The final classifier reached a Cohen's kappa score of 0.55. The table below shows the species-specific performance of the classifier.
|  | precision | recall | f1-score |
|--|--|--|--|
| Birch | 0.46 | 0.62 | 0.52 |
| Deadwood | 0.50 | 0.25 | 0.33 |
| European aspen | 0.81 | 0.70 | 0.75 |
| Norway spruce | 0.54 | 0.45 | 0.49 |
| Scots pine | 0.77 | 0.83 | 0.80 |


### Creating a wall-to-wall tree map
The final phase of the tree detection and classification process was to create a wall-to-wall tree map of the study area. The final tree species classifier was used for predicting a species for each delineated tree segment within the study area. In total, 1,787,251 trees were delineated and classified in the study  area. The table below shows the species-specific numbers of tree segments.
|Species| Number of segments |
|--|--|
| Birch | 326,471 |
| Deadwood | 26,739 |
| European aspen | 85,091 |
| Norway spruce | 505,784 |
| Scots pine | 843,166 |

**Note!** The species-distribution in the training and test sets differed from the true species distribution, as the ground reference data were collected using field plots and individual tree measurements. More specifically, the collection of the ground reference data included individual tree measurements of aspens and dead trees, and thus these two classes were overrepresented in the training and test datasets. As a result, the evaluated performance of the final tree species classifier does not fully reflect the accuracy of the generated tree map. Please see section 2.3 in Mäyrä et al. (2021) for a more detailed description on how the ground reference data were collected.
