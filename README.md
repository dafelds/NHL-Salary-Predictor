# NHL-Salary-Predictor

The core intention of this project was to create a salary predictor based on performance metrics. The project uses NHL statistics simply because professional sports is an industry where salary and performance metrics are readily available. The idea is that the model generated here can be modified to be used within any company that measures staff performance, though with a caution to be aware of intrinsic bias within the data. With this model being contextualized by the NHL, age has been consciously chosen to be incorporated as part of the feature space for the model since it is well understood that age plays a factor in performance, and by extension salary, in professional sports. Were this model to be used in other industries this would be a clear ethical violation.

### File Structure

#### src
##### modules folder
This folder contains all of the functions that were used in collection of the data and creation of the predictive model. To recreate the player performance dataset, simply run the data_mining script.

#### data folder
This folder holds the player performance data as well as the player salary data.