from PIL import Image
from numpy import *
from collections import Counter , defaultdict
import sys



def encode(raw_data,dict,block_size):  #raw data as an array or a list 
    length = len(raw_data)
    r = length%block_size
    encoded_data = []
    if(r != 0): 
        for p in range (block_size - r): #add padding
            raw_data= append(raw_data,raw_data[0])
        length = len(raw_data)
    for i in range(length//block_size):
        c = encode_unit(raw_data , dict , i*block_size , block_size) #encode each block separately
        encoded_data.append(c)
    return encoded_data


def encode_unit(data , dict , offset , block_size):# takes a dict {char : (lower , higher)}
    p=1 #probability of the first level 
    code = 0 
    l  = offset + block_size #encode starting with the nth block
    for i in range(offset , l):
        code += dict[data[i]][0] * p #add the current level and the current probability to the block code
        if(i == l -1 ): # take the average of the last lower and upper bounds
            code = (2 * code +  (dict[data[i]][1] - dict[data[i]][0])  * p) / 2
        p *= (dict[data[i]][1]-dict[data[i]][0]) # next lvl  =  probability of the last level * the probability of the pixel 
    return code


def decode(encoded_data , dict , raw_length , block_size):
    decoded_data = []
    for c in encoded_data:
        decode_unit(decoded_data , c , dict ,block_size)
    if(raw_length % block_size):
        for i in range (block_size - raw_length % block_size): # remove padding
            decoded_data.pop()
    return decoded_data



def decode_unit(decoded , encoded , decode_dict , length): #takes a sorted list [(char , lower , higher)]
    l = 0 
    h = 1
    for i in range(length):
        x = binary_search(encoded,decode_dict,l,h-l,0,len(decode_dict))
        if(x is None):
            #if the code wasn't found due to float percesion add the last pixel instead
            decoded.append(decoded[len(decoded) -1])
        else :
            l = x[1]
            h = x[2]
            decoded.append(x[0])
    return decoded



def binary_search(code,d,lower,p,left,right): # binary search that checks the bounderies
    if(left <= right):
        i = left + (right - left) // 2
        if(i>=len(d)):
            return
        l = lower +p * d[i][1];
        h = l + p* (d[i][2]-d[i][1])
        if ( code >= l and code < h  ):
            res = (d[i][0] , l , h)
            return res
        elif(code < l):
            return binary_search(code,d,lower,p,left,i-1)
        elif(code > h):
            return binary_search(code,d,lower,p,i+1,right)
    else:
        raise ValueError('Could Not Decode ' + str(code))

def read_image(input_file , f):
    img = Image.open(input_file).convert("L") #read an Image and convert it into a grayscale image 
    arr = array(img).flatten() #flatten the image 
    #build a counter of the probability of each pixel 
    c = Counter(arr)  # count each pixel 
    prob_arr = arange(256 , dtype='float' + str(f))
    for p in c:
        c[p] =c[p] / len(arr)
    for i in range(256): #create the 1d array to be saved 
        prob_arr[i] = c[i]
    save('prob',prob_arr)
    return arr

def get_dict():
    encode_dict  = []
    try:
        prob_arr = load('prob.npy') 
    except:
         raise("Can't find porb.npy")
    for p in enumerate(prob_arr):
        if (p[1]):
            encode_dict.append((p[0],p[1])) #builds a dict to encode with 
    encode_dict.sort(key=lambda x:x[1], reverse=True)  #sort the dict so we can apply binary search
    return encode_dict

if len(sys.argv) != 6 and len(sys.argv) != 7 :
    raise('Wrong input.\nEnter encode <input_file> <output_file> <block_size>  <float_size> to encode your file or \n\
        Enter decode <input_file> <output_file> <width> <height> <block_size> to decode your file')


if sys.argv[1] == 'encode':
    try:
        input_file = sys.argv[2]
        output_file = sys.argv[3]
        block_size = int(sys.argv[4])
        float_size = sys.argv[5] 
        image = read_image(input_file , float_size)
        counter = get_dict()
        d = defaultdict(list)
        sum = 0 
        for i in counter:
            d[i[0]] = (sum , sum + i[1])
            sum += i[1]
        encoded = encode(image,d,block_size)
        encoded = array(encoded,dtype='float' + str(float_size))
        save(output_file , encoded )
    except:
        raise('please choose a valid input')
elif sys.argv[1] == 'decode':
    if(len(sys.argv) != 7):
        raise('Wrong input.\nEnter decode <input_file> <output_file> <width> <height> <block_size> to decode your file')
    try:
        input_file = sys.argv[2]
        output_file = sys.argv[3]
        width = sys.argv[4]
        height = sys.argv[5]
        block_size = int(sys.argv[6])
        length = int(width) * int(height)
        en_dict = get_dict()
        encoded = load(input_file)
        print(type(encoded[0]))
        decode_dict = []
        sum = 0 
        for i in en_dict:
            decode_dict.append((i[0],sum , sum + i[1]))
            sum += i[1]
        photo = decode(encoded , decode_dict ,length,block_size)
        p = reshape(array(photo , dtype = 'uint8'),(-1 ,int(width)))
        image = Image.fromarray(p)
        image.save(output_file)
    except:
        raise('please enter valid inputs')




