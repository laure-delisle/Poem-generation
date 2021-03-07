#######################################################################
#
#    Helper functions for Caltech's CS155 mini project:  Poem Generation
#
#    Authors: Lauren Conger, Laure Delisle
#    Year: 2021
#
#######################################################################
import re
import numpy as np
import pandas as pd


def load_syllable_data():
    """    Generate the syllable dataframe mapping words to syllable counts
        output:
            syllable_df, a pd.Dataframe with columns:
                word (str)
                syllables (int): # of syllables for word
                other_syllables (int): alternative # of syllables for word
                end_linesyllables (int): # of syllables for word if word is last on line
    """

    # Load syllable data
    sd_headers = ["word","syllables1","syllables2"]
    syllable_df = pd.read_csv('https://raw.githubusercontent.com/lakigigar/Caltech-CS155-2021/main/projects/project3/data/Syllable_dictionary.txt',delimiter=' ',names=sd_headers,na_values=[''])

    # swap E (end) syllables with syllables in last column
    idx = syllable_df['syllables1'].isin(['E1','E2','E3','E4','E5','E6','E7','E8','E9','E10'])
    syllable_df.loc[idx,['syllables1','syllables2']] = syllable_df.loc[idx,['syllables2','syllables1']].values

    # now change the names of the columns
    syllable_df = syllable_df.rename(columns={"syllables1": "syllables", "syllables2": "end_linesyllables"})

    # drop the E's; separate out words with two pronounciations
    idx = ~syllable_df['end_linesyllables'].isnull()
    split_vals = syllable_df.loc[idx,'end_linesyllables'].values
    end_syl = []
    second_syl = []
    for val in split_vals:
        if 'E' in val:
            end_syl.append(list(val)[1])
            second_syl.append(np.NaN)
        else:
            end_syl.append(np.NaN)
            second_syl.append(val)

    # add these back into dataframe
    idx_values = [i for i, x in enumerate(idx) if x]
    syllable_df.at[idx_values,'end_linesyllables'] = end_syl
    syllable_df['other_syllables'] = np.NaN
    syllable_df.at[idx_values,'other_syllables'] = second_syl

    # cast everything to float
    for column in ["syllables", "end_linesyllables", "other_syllables"]:
    	syllable_df[column] = syllable_df[column].apply(lambda x: float(x))

    return syllable_df



def load_shakespeare_data():
    """ Generate the shakespeare dataframe, containing lines from all sonnets, extracting info about each line
        output:
            shakespeare_df, a pd.Dataframe with columns:
                line (str): line from a Shakespeare sonnet
                sonnet_number (int): sonnet id the line is from
                linenumber (int): line id in the sonnet the line is from
    """

    # Load Shakespeare data
    shakespeare_df = pd.read_fwf('https://raw.githubusercontent.com/lakigigar/Caltech-CS155-2021/main/projects/project3/data/shakespeare.txt',names=["line"])

    # delete sonnet numbers
    idx_values = [i for i, x in enumerate(shakespeare_df['line'].str.isnumeric()) if x]
    shakespeare_df['sonnet_number'] = 0
    shakespeare_df['linenumber']     = 0

    # loop over indices to label lines
    for ii,idx in enumerate(idx_values):
        if ii == 0:
            sonnet_idx = [i for i, x in enumerate(shakespeare_df.index < idx_values[ii+1]) if x]
            shakespeare_df.at[sonnet_idx,'sonnet_number'] = ii+1
            shakespeare_df.at[sonnet_idx,'linenumber']   = np.arange(0,len(sonnet_idx),1)
        else:
            sonnet_idx = [i for i, x in enumerate(shakespeare_df.index >= idx_values[ii]) if x]
            shakespeare_df.at[sonnet_idx,'sonnet_number'] = ii+1
            shakespeare_df.at[sonnet_idx,'linenumber']   = np.arange(0,len(sonnet_idx),1)

    # delete temporary index
    shakespeare_df = shakespeare_df.drop(index=idx_values)

    return shakespeare_df



def get_syllables(line, words_with_syllable_count, syllable_df):
    """ Helper function: creates list of syllable counts according to syllable_df for a given list of words
        inputs:
            line (list(str)): list of parsed words
            words_with_syllable_count (list): list of words for which we know the syllable count
            syllable_df (pd.Dataframe): words, and number of syllables (includes alternative and end-of-line)
        output:
            syl_list (list(int)): list of syllable counts corresponding to input words

    """
    syl_list = []
    for idx,word in enumerate(line):
        word = word.lower()

        # deal with those nasty apostrophes
        if word not in words_with_syllable_count:
            word = word.strip("'")

        # last word in line: check for alternative pronunciation
        if (idx == len(line)-1):
            last_syl = syllable_df.loc[syllable_df['word']==word,'end_linesyllables']
            # alternative pronunciation exists
            if len(last_syl) > 0:
                try:
                    syl = int(syllable_df.loc[syllable_df['word']==word,'end_linesyllables'])
                except:
                    syl = int(syllable_df.loc[syllable_df['word']==word,'syllables'])
            # regular pronunciation only
            else:
                try:
                    syl = int(syllable_df.loc[syllable_df['word']==word,'end_linesyllables'])
                except:
                    syl = 0
                    # if word == '': print("Last syllable error 2:", "empty")
                    # if word == ' ': print("Last syllable error 2:", "space")
        # word is not the last word in line: 
        else:
            try:
                syl = int(syllable_df.loc[syllable_df['word']==word,'syllables'])
            except:
                syl = 0
                # if word == '': print("Last syllable error 2:", "empty")
                # if word == ' ': print("Last syllable error 2:", "space")
        
        # add this pronunciation to the list
        syl_list.append(syl)

    #print(syl_list)
    return syl_list



def parse_shakespeare_for_syllables(shakespeare_df, syllable_df):
    """ Parse lines from shakespeare_df into list of words, extract syllable count for each word from syllable_df
        output:
            shakespeare_syllables_df, a pd.Dataframe with columns:
                line (list(str)): TODO
                syllable_count
    """

    # copy matrix for split words
    shakespeare_syllables_df = shakespeare_df.copy()

    # parse words
    shakespeare_syllables_df['line'] = shakespeare_syllables_df['line'].apply(lambda x: re.findall(r"[\w'-]+", x))

    # produce list of syllable count
    words_with_syllable_count = list(syllable_df['word'])

    # parse lines for syllable counts
    shakespeare_syllables_df['syllable_count'] = shakespeare_syllables_df['line'].apply(
        lambda x: get_syllables(x, words_with_syllable_count, syllable_df))
    
    return shakespeare_syllables_df[['line', 'syllable_count']]



def encode_words_to_int(line, dict_word_to_int):
	""" Helper function: encodes words in word_list to integers
		input:
			line (list(str)): words to encode
			dict_word_to_int (dict): mapping word->int
		output:
			encoded (list(int)): integer-encoded word list
	"""
	encoded = []
	words_with_syllable_count = dict_word_to_int.keys()

	for word in line:
		# lower case
		word = word.lower()

		# deal with those nasty apostrophes
		if word not in words_with_syllable_count:
			word = word.strip("'")
		# deal with empty
		if word in ["", " ", "'"]:
			continue

		try:
			encoded.append(dict_word_to_int[word])
		except:
			continue

	return encoded



def encode_shakespeare(shakespeare_syllables_df, syllable_df):
	""" Encode lines into integers
		inputs:
			shakespeare_syllables_df (pd.Dataframe): dataframe with parsed lines
			syllable_df (pd.Dataframe): dataframe with all words in our vocabulary
		outputs:
			dict_word_to_int (dict): mapping word->int
			shakespeare_encoded_df (pd.Dataframe): lines and associated encoding (list of int) 
	"""
	shakespeare_encoded_df = shakespeare_syllables_df.line.copy().to_frame()

	# each word in the vocabulary is associated to an int 
	dict_word_to_int = dict(zip(syllable_df['word'], syllable_df.index))

	# encode each line into integers
	shakespeare_encoded_df['encoded'] = shakespeare_syllables_df['line'].apply(lambda x: encode_words_to_int(x, dict_word_to_int))

	return dict_word_to_int, shakespeare_encoded_df



def get_X():
	""" Load and pre-processes data, returns an observation matrix, and useful tidbits (word->int mapping, syllable counts)
		output:
			X (list(list(int))): encoded observations, each row is an integer-encoded line of a sonnet
			dict_word_to_int (dict): mapping word->int for all words in the vocabulary
			shakespeare_syllables_df (pd.Dataframe): lines and their corresponding syllable count lists
	"""
	syllable_df = load_syllable_data()
	shakespeare_df = load_shakespeare_data()
	print("Loading done")

	# parsing
	shakespeare_syllables_df = parse_shakespeare_for_syllables(shakespeare_df, syllable_df)
	print("Parsing done")

	# encoding
	dict_word_to_int, shakespeare_encoded_df = encode_shakespeare(shakespeare_syllables_df, syllable_df)
	print("Encoding done")

	# compile encoded lines into observation matrix X
	X = [encoded_line for encoded_line in shakespeare_encoded_df['encoded']]
	print("X done")

	return X, dict_word_to_int, shakespeare_syllables_df

