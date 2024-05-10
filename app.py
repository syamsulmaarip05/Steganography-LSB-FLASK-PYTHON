from flask import Flask, render_template, request, send_file, flash, redirect, url_for, session
from PIL import Image
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)
UPLOAD_FOLDER = 'static/uploads/'
app.secret_key = "SYAMSUL SALMAN KINAN"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Fungsi untuk memeriksa apakah ekstensi file diizinkan
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Fungsi untuk encoding pesan ke dalam gambar
def encode_enc(image, data, key):
    def genData(data):
        newd = []
        for i in data:
            newd.append(format(ord(i), '08b'))
        return newd

    def modPix(pix, data):
        datalist = genData(data)
        lendata = len(datalist)
        imdata = iter(pix)

        for i in range(lendata):
            pix = [value for value in imdata.__next__()[:3] +
                                    imdata.__next__()[:3] +
                                    imdata.__next__()[:3]]

            for j in range(0, 8):
                if (datalist[i][j] == '0' and pix[j] % 2 != 0):
                    pix[j] -= 1
                elif (datalist[i][j] == '1' and pix[j] % 2 == 0):
                    if(pix[j] != 0):
                        pix[j] -= 1
                    else:
                        pix[j] += 1
            if (i == lendata - 1):
                if (pix[-1] % 2 == 0):
                    if(pix[-1] != 0):
                        pix[-1] -= 1
                    else:
                        pix[-1] += 1
            else:
                if (pix[-1] % 2 != 0):
                    pix[-1] -= 1
            pix = tuple(pix)
            yield pix[0:3]
            yield pix[3:6]
            yield pix[6:9]

    newimg = image.copy()
    w = newimg.size[0]
    (x, y) = (0, 0)

    for pixel in modPix(newimg.getdata(), key + data):  # Menambahkan kunci ke data sebelum encoding
        newimg.putpixel((x, y), pixel)
        if (x == w - 1):
            x = 0
            y += 1
        else:
            x += 1

    return newimg

# Fungsi untuk decoding pesan dari gambar
def decode_dec(image, key):
    data = ''
    imgdata = iter(image.getdata())

    while (True):
        pixels = [value for value in imgdata.__next__()[:3] +
                                imgdata.__next__()[:3] +
                                imgdata.__next__()[:3]]

        binstr = ''

        for i in pixels[:8]:
            if (i % 2 == 0):
                binstr += '0'
            else:
                binstr += '1'

        data += chr(int(binstr, 2))
        if (pixels[-1] % 2 != 0):
            break

    if not data.startswith(key):
        return "Kunci salah!"
    
    return data[len(key):]


@app.route('/')
def index():
    # Periksa jika ada hasil encoding dalam session
    encoding_result = session.pop('encoding_result', None)
    if encoding_result:
        return render_template('index.html', filename=encoding_result['filename'], encoded_image_path=encoding_result['encoded_image_path'])
    
    # Periksa jika ada hasil decoding dalam session
    decoding_result = session.pop('decoding_result', None)
    if decoding_result:
        return render_template('decode.html', decoding_result=decoding_result)
    
    return render_template('index.html')

@app.route('/encode', methods=['POST'])
def encode():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No image selected for uploading')
        return redirect(request.url)
        
    if file and allowed_file(file.filename):
        message = request.form['message']
        key = request.form['key']
        image = Image.open(file)
        encoded_image = encode_enc(image, message, key)
        encoded_image_filename = secure_filename(file.filename.split('.')[0] + '_encoded.png')
        encoded_image_path = os.path.join(app.config['UPLOAD_FOLDER'], encoded_image_filename)
        encoded_image.save(encoded_image_path)
        session['encoding_result'] = {
            'filename': encoded_image_filename,
            'encoded_image_path': encoded_image_path
        }
        flash('Image successfully encoded')
        return redirect(url_for('index'))



@app.route('/decode', methods=['POST'])
def decode():
    if 'file' not in request.files:
        flash('No file part')
        return redirect(request.url)
    
    file = request.files['file']
    if file.filename == '':
        flash('No image selected for uploading')
        return redirect(request.url)
        
    if file and allowed_file(file.filename):
        key = request.form['key']
        image = Image.open(file)
        decoded_message = decode_dec(image, key)
        session['decoding_result'] = decoded_message
        flash('{}'.format(decoded_message))
        return redirect(url_for('index2'))

@app.route('/index2')
def index2():
    return render_template('decode.html')

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

if __name__ == "__main__":
    app.run(debug=True)

