import csv

def trans_to_csv(trans_total, region_id):
    "Outputs state transmission data to csv file, requires input from region_transmission_data."
    #adding in state based row and column names for trans_total output to csv
    csv_output = [[0 for col in range(6)] for row in range(6)]
    # adding in transmission values
    for i in range(0, 5):
        for j in range(0, 5):
            csv_output[i+1][j+1] = trans_total[i][j]
    # adding in row and column names strings
    for i in range(0, 6):
        for j in range(0, 6):
            if ((i > 0) and  (j == 0)):
                csv_output[i][j] = region_id[i-1]
            elif ((i == 0) and (j > 0)):
                csv_output[i][j] = region_id[j-1]
            else:
                continue
    #writing to csv
    with open("trans_total.csv", "w", newline='') as csv_file:
        csv_wr = csv.writer(csv_file)
        csv_wr.writerows(csv_output)
