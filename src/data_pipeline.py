import pandas as pd
from dask.distributed import Client
import dask.dataframe as dd
import string
from zxcvbn import zxcvbn

#TODO Planned implementation in future version
'''
spark_available = True
try: 
    from pyspark import SparkContext as sc
    from pyspark.sql import SparkSession
except:
    spark_available = False
try:
    spark = SparkSession.builder.appName('Passwords').getOrCreate()
except:
    print("Errors with starting SparkSession")
'''


class DataSet():
    """Intended to provide modularity and inheritance of data pipeline\
         for different types and sizes of password datasets
    """
    #TODO Planned implementation in future version
    def __init__(self, filepath: str, delimiter: str, df_type: str='pandas'):
        self.filepath = filepath
        self.delimiter = delimiter
        self.df_type = identify_dataframe_type(df_type)

    def identify_dataframe_type(self, df_type):
        """Sets the class' dataframe attribute based on the passed in argument
        Args:
            df_type (str): User-friendly method of indicating desired dataframes\
                 and operations.
        Usage:
            A user seeking to analyze large datasets will want to pass in the \
                dask or spark arguments to use the multi-processor libraries.
        
        Returns:
            self.df_type (DataFrame): assigned to class' attribute
        """
        if df_type == 'dask':
            self.df_type = dd.core.DataFrame
        elif df_type == 'pandas':
            self.df_type = pd.core.frame.DataFrame
        elif df_type == 'spark':
            print('pyspark DataFrame not yet implemented')
            self.df_type = pd.core.frame.DataFrame
        return self.df_type
        
#TODO Planned implementation in future version
'''
class daskDataSet(DataSet):
    def __init__(self):

class pysparkDataSet(DataSet):
    def __init__(self):
'''

def pass_class(password: str):
        """Returns the "password class" for the given password argument - a character count

        Args:
            password (str): a single password to be parsed for character composition

        Returns:
            (f-str): The "password class" in Can$ order\
                (C-uppercase, a-lowercase, n-numbers, $-symbols)

        Usage:
            Intended for use in generating a DataFrame column \
                for further data analysis of character composition in passwords.
        """
        lower = set(string.ascii_lowercase)
        upper = set(string.ascii_uppercase)
        number = set(string.digits)
        count_dict = {
            'lower': 0,
            'upper': 0,
            'number': 0,
            'symbol': 0
        }

        for char in password:
            if char in upper:
                count_dict['upper'] += 1
            elif char in lower:
                count_dict['lower'] += 1
            elif char in number:
                count_dict['number'] += 1
            else:
                count_dict['symbol'] += 1

        return f"{count_dict['upper']},{count_dict['lower']},{count_dict['number']},{count_dict['symbol']}"

def pass_class_expand(df: pd.core.frame.DataFrame):
    """Expands the "password class" column into four new DataFrame columns\
        each with a character type count.

    Args:
        df (pd.core.frame.DataFrame): DataFrame that has a column generated by pass_class function
    """
    class_split = df['class'].str.split(pat=',', expand=True, n=3)
    df['upper'] = class_split[0]
    df['lower'] = class_split[1]
    df['number'] = class_split[2]
    df['symbol'] = class_split[3]
    
    if isinstance(df, pd.core.frame.DataFrame):
        df.drop('class', axis=1, inplace=True)
    else:
        df = df.drop('class', axis=1)

def zxcvbn_score(password: str):
    """Runs the zxcvbn function and returns the password score

    Args:
        password (str): any password you would commonly find, usually of length <40.

    Returns:
        password score (int): score from 0-4, with 4 being an ideal "strong" password.
    """
    return zxcvbn(password)['score']

def zxcvbn_guesslog(password: str):
    """Runs the zxcvbn function and returns the password max estimate of \
        guesses needed to crack in log_10 scale.

    Args:
        password (str): any password you would commonly find, usually of length <40.

    Returns:
        (float): password max estimate of guesses needed to crack in log_10 scale\
            will be less than the password's length.
    """
    return zxcvbn(password)['guesses_log10']

def strength_features(df: pd.core.frame.DataFrame):\
    """Creates 'score' and 'guesses_log' columns in passed DataFrame based on\
        having a 'password' column ready for application of the zxcvbn function.
    """
    df['score'] = df['password'].apply(zxcvbn_score)
    df['guesses_log'] = df['password'].apply(zxcvbn_guesslog)
    # df['time_guess'] = df['password'].apply(zxcvbn)['']

def to_csv(df, filename: str='../data/data.csv'):
    """Saves passed DataFrame to file directory.
    Selects Dask or Pandas implementation for optimizations.

    Args:
        df (pd.core.frame.DataFrame): Processed DataFrame in need of saving.
        filename (str, optional): Custom filename and directory lcoation.\
            Defaults to '../data/data.csv'.
    """
    if isinstance(df, dd.core.DataFrame):
        df.to_csv(filename, single_file=True)
    else:
        df.to_csv(filename, index=False)

def standardize_10msample(frac: float=0.01):
    """Runs each data processing function in series to save a new .csv data file.
    Intended for Pandas DataFrame. For Dask DataFrames, use standardize_10msample_dask

    Args:
        frac (float, optional): Fraction of data file rows to sample. Defaults to 0.01.

    Returns:
        df_10msample(pd.core.Frame.DataFrame): Finished DataFrame\
             ,that should match the same when using .read_csv() method
    """
    sample_10m = '../data/10m_sample_common_passwords/10-million-combos.txt'
    df_10msample = pd.read_csv(sample_10m, header=None, delimiter='\t').astype(str).sample(frac=frac)
    df_10msample.columns = ['username', 'password']
    df_10msample.drop('username', axis=1, inplace=True)
    df_10msample['length'] = df_10msample['password'].apply(len)
    strength_features(df_10msample)
    df_10msample['class'] = df_10msample['password'].apply(withPassClass)
    pass_class_expand(df_10msample)
    to_csv(df_10msample, filename='../data/10m_sample_common_passwords/10m_standardized.csv')
    return df_10msample

def standardize_10msample_dask(frac: float=0.01):
    """Runs each data processing function in series to save a new .csv data file.
    Intended for Dask DataFrame. For Pandas DataFrames, use standardize_10msample.

    Args:
        frac (float, optional): Fraction of data file rows to sample. Defaults to 0.01.

    Returns:
        df_10msample(dd.core.DataFrame): Finished DataFrame\
             ,that should match the same when using .read_csv() method
    """
    sample_10m = '../data/10m_sample_common_passwords/10-million-combos.txt'
    df_10msample = dd.read_csv(sample_10m, header=None, delimiter='\t').astype(str).sample(frac=frac)
    df_10msample.columns = ['username', 'password']
    df_10msample = df_10msample.drop('username', axis=1)
    df_10msample['length'] = df_10msample['password'].apply(len, meta=('password', 'str'))
    strength_features(df_10msample)
    df_10msample['class'] = df_10msample['password'].apply(withPassClass, meta=('class', 'str'))
    pass_class_expand(df_10msample)
    to_csv(df_10msample, filename='../data/10m_sample_common_passwords/10m_standardized.csv')
    return df_10msample

if __name__ == '__main__':
    test_read = '../data/10m_sample_common_passwords/test_read.txt'
    test_write = '../data/test_write.txt'

    sample_10m_path = '../data/10m_sample_common_passwords/10-million-combos.txt'
    #! Uncomment below function in order to begin process of standardizing data
    #! a frac=1.0 run can take upwards of 6 hours due to use of pandas DataFrame  
    # standardize_10msample(sample_10m_path, frac=0.001)


    linkedin_path = '../data/linkedin_leak/linkedin_hash_plain.txt'
    # df_linkedin = pd.read_csv(linkedin_path, header=None, delimiter='\n')

    rockyou_path = '../data/rockyou_leak/rockyou_copy.txt'
    # df_rockyou = pd.read_csv(rockyou_path, delimiter='\n')

    pwned_path = '../data/have_i_been_pwned_v4/been_pwned_v4_hash_plain.txt'
    # df_pwned = pd.read_csv(pwned_path, header=None, \
    #         delimiter='\n', columns='password')
    #         .astype(str)



