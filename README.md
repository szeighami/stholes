# Differentially Private STHoles

This repository contains a differentially private (DP) adaptaion of STHOles [1]. It utilizes a query workload to build a histogram of data points. 

## To run

Call python main.py to run the program. It requires numpy and pandas library.

## DP Adaptation Details
Our DP-compliant STHoles implementation makes two adjustments to the original STHoles algorithm to allow for better accuracy when accounting for privacy. First, we allow the algorithm to use unlimited memory, so that it does not need to merge any of the buckets to reduce memory usage. This not only avoids incurring the merge penalty (discussed in the paper [1]) but also lowers the privacy budget consumption, since we can avoid calculating merge penalties that would require budget consuming accesses to $D$. Second, we separate the process of calculating the frequency counts for each bucket from the process of building the nested bucket structure. That is, we first build the bucket structure based on the query workload and then calculate the frequency counts within each bucket. This separation significantly reduces the privacy budget consumption, since it allows us to avoid asking overlapping queries from the database and thus, final privacy budget accounting can be done with only parallel composition theorem. Next, we present how we build the buckets and calculate the frequency counts in more details.

First, we generate the nested budget structure using the query workload . Modified from the original algorithm, in this step, we do not calculate database related statistics such as the number of records in each bucket as that would necessitate spending scarce privacy budget. For the same reason, we also skip the step which merges buckets together based on a penalty caculated from database records. From the privacy analysis perspective, the query workload is public and using information therein incurs no privacy leakage. Hence, the first step doesn't use any privacy budget. In the second step, we generate sanitized frequency counts for STHoles' buckets in the data structure. For each bucket, we query the database for the number of records that fall within its extent, sanitizing these counts using the Laplace Privacy Mechanism.

## References
[1] Nicolas Bruno, Surajit Chaudhuri, and Luis Gravano. 2001. STHoles: A Multidi-mensional Workload-Aware Histogram. InProceedings of the 2001 ACM SIGMODInternational Conference on Management of Data. Association for ComputingMachinery, New York, NY, USA, 211–222
