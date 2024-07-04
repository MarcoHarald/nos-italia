n_pics = 20 # images to display
n_cols = n_cols # images per row 
n_rows = int(1+n_pics // n_cols) # calculate number of rows
rows = [st.columns(n_cols) for _ in range(n_rows)] # define row IDs
cols = [column for row in  rows for column in row] # define col IDs
