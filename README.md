<div align="center">

# 🏊‍♂️🚴‍♂️🏃‍♂️ **TRIATHLON**  
### _Integrated Triathlon Lifestyle Platform_

</div>

---

## 👥 **Anggota Kelompok**
| Nama | NPM |
|------|------|
| Jarred Muhammad Raditya | 2406432425 |
| Justin Dwitama Seniang | 2406406742 |
| Muhammad Helmi Alfarissi | 2406402416 |
| Muhammad Kaila Aidam Riyan | 2406404781 |
| Randuichi Touya | 2406350021 |
| Syakirah Zahra Dhawini | 2406353950 |

---

## 🧭 **Deskripsi Aplikasi**

Di tengah meningkatnya tren gaya hidup sehat dan popularitas olahraga ketahanan (endurance sports) seperti lari, sepeda, dan renang di Indonesia, muncul sebuah tantangan besar: **fragmentasi ekosistem digital.**

Data menunjukkan bahwa para pegiat olahraga ini seringkali harus berpindah-pindah platform untuk memenuhi kebutuhan mereka:

> Perjalanan digital seorang atlet saat ini sangat terpecah-belah. Mereka memulai dengan aplikasi pelacak seperti Strava untuk mencatat setiap detail jarak dan durasi latihan. Untuk kebutuhan sosial, seperti berdiskusi dan mencari teman berlatih, mereka beralih ke media sosial layaknya Facebook. Saat membutuhkan peralatan baru, mereka harus membuka aplikasi e-commerce seperti Tokopedia atau Shopee. Bahkan untuk hal mendasar seperti memesan kolam renang atau stadion, mereka masih sering dihadapkan pada sistem pemesanan manual, membuktikan betapa tersebarnya semua kebutuhan mereka di berbagai platform yang berbeda.

Fragmentasi ini menciptakan **inefisiensi** dan **memecah belah pengalaman pengguna.**  
Seorang atlet harus mengelola banyak akun, komunitasnya tersebar, dan sulit menemukan semua yang dibutuhkan dalam satu tempat.

**Triathlon** lahir sebagai solusi dari masalah ini. Aplikasi kami adalah **sebuah platform terintegrasi** yang dirancang khusus untuk komunitas olahraga ketahanan di Indonesia. Kami menyiapkan semua kebutuhan atlet dan para peminat olahraga—mulai dari **pelacakan aktivitas, interaksi komunitas, jual-beli perlengkapan, hingga pemesanan fasilitas**—ke dalam **satu ekosistem yang solid dan mudah diakses.**

---

## 🌱 **Kebermanfaatan (Value Proposition)**

Triathlon memberikan nilai lebih bagi setiap aktor dalam ekosistem olahraga:

### 👤 Bagi Atlet (User)
Menyediakan **one-stop solution** yang menyederhanakan perjalanan olahraga mereka.  
Dari mencatat kemajuan pribadi, berdiskusi dengan sesama pegiat, membeli perlengkapan, hingga memesan tempat latihan — semua dapat dilakukan tanpa meninggalkan aplikasi.

### 💼 Bagi Penjual (Seller)
Menawarkan **akses langsung ke pasar yang sangat tertarget.**  
Penjual dapat dengan mudah menjangkau komunitas atlet yang relevan dan membutuhkan produk mereka.

### 🏟️ Bagi Pengelola Fasilitas (Facility Administrator)
Membuka **kanal pemasaran baru** dan menyederhanakan proses manajemen pemesanan, meningkatkan visibilitas dan okupansi fasilitas.

Dengan menyatukan komunitas dan layanan, **Triathlon tidak hanya menjadi sebuah aplikasi**, tetapi **sebuah pusat digital yang mendukung pertumbuhan gaya hidup aktif di Indonesia.**

---

## 🧩 **Daftar Modul yang Akan Diimplementasikan**

### 1. 👤 User Profile — _Helmi_
Modul **User Profile** memungkinkan pengguna memiliki beberapa peran (_User, Seller, Facility Administrator_) dan melakukan **switch role** pada halaman profil. Tampilan data akan menyesuaikan role aktif:

- **User:** menampilkan aktivitas olahraga (Activities), forum post, dan review di Place Recommendation.  
- **Seller:** menampilkan daftar produk yang dijual (Shop).  
- **Facility Administrator:** menampilkan daftar fasilitas yang dikelola, opsi tambah fasilitas, serta daftar tiket pemesanan (Ticket).

Selain itu, modul ini juga berpengaruh pada Profile View ketika pengguna lain melihat halaman profil seseorang: data yang ditampilkan tetap bergantung pada role aktif dari pemilik profil tersebut.

Implementasi pola **MVT Django**:
- **Model:** menyimpan data user profile, role, dan relasi dengan modul lain.  
- **View:** menentukan tampilan data sesuai role aktif dan menyediakan endpoint untuk switch role.  
- **Template:** menggunakan tampilan berbeda untuk setiap role, baik untuk tampilan diri sendiri maupun saat profil dilihat orang lain.

---

### 2. 💬 Forum — _Aidam_
Modul **Forum** memungkinkan user membuat, membaca, dan berinteraksi melalui **threads dan replies**, sistem diskusi terinspirasi Hypixel Forums.  
Fitur utama:
- Sistem **bumping otomatis** ketika ada balasan baru pada sebuah thread.
- Pengguna dapat memfilter thread berdasarkan kategori, popularitas, dan filter lainnya.

Fungsionalitas per peran:
- **User:** dapat membuat thread baru, membalas thread, melakukan edit atau delete pada post miliknya, serta memberi upvote/downvote pada thread atau balasan. 
- **Admin:** memiliki kemampuan moderasi seperti menghapus thread, mengunci diskusi, atau menandai thread tertentu sebagai pinned.


**Implementasi MVT Django:**
- **Model:**  Menyimpan data thread, reply, category dan upvote/downvote. Setiap thread memiliki atribut seperti judul, isi, pembuat, waktu dibuat, waktu terakhir dibalas, jumlah upvote/downvote, serta relasi ke kategori. Reply menyimpan isi balasan, pengirim, dan waktu. Field last_activity pada thread akan diperbarui setiap kali ada balasan baru untuk mendukung mekanisme thread dengan aktivitas terakhir di atas.  
- **View:** Mengelola logika untuk menampilkan daftar thread yang otomatis diurutkan berdasarkan recent activity, menampilkan detail thread beserta balasannya, memproses pembuatan, pengeditan, dan penghapusan thread atau reply, dan menangani upvote/downvote serta filtering.
- **Template:**  Menyediakan tampilan halaman utama forum dengan daftar thread yang bisa difilter. Halaman detail thread dengan daftar balasan secara hierarkis. Formulir untuk membuat thread baru dan membalas thread. Tombol interaksi seperti reply, edit, delete, upvote/downvote, dan filter dropdown.

---

### 3. 🛒 Shop — _Jarred_
Modul **Shop** memungkinkan pengguna berperan sebagai:
- **User:** melihat-lihat katalog, memasukkan produk ke keranjang, memasukkan produk ke wishlist dan melakukan pembelian.
- **Seller:** menambahkan produk, mengedit produk, dan menghapus produk.  
- **Admin:** menghapus produk dari semua user.

**Implementasi MVT Django:**
- **Model:** Menyimpan nama, harga, stok, category, thumbnail, description dari produk.
- **View:** Mengelola logika untuk menampilkan produk-produk yang dijual oleh masing-masing pengguna dan juga pengguna dapat melakukan aksi jual beli.  
- **Template:** Menyediakan interface untuk menampilkan semua produk, menambahkan produk, mengedit produk, menghapus produk, melakukan pembelian.
---

### 4. 🏃 Activities — _Touya_
Modul **Activities** memungkinkan pengguna untuk menyimpan data kegiatan olahraga mereka dalam aplikasi. Kegiatan tersebut disimpan pribadi setiap user pada page khusus, mirip user profile. Pada page ini, user dapat melihat kegiatan mereka sebelumnya, me-log aktivitas baru, melihat data aktivitas lebih rinci, dan melihat beberapa statistik yang ditampilkan berdasarkan aktivitas mereka.

**Implementasi MVT Django:**
- **Model:** Menyimpan tempat kegiatan, tipe olahraga, durasi olahraga, timestamp olahraga, jarak tempuh, notes, calories burned 
- **View:** Menyediakan logic untuk menambahkan Activity baru, melihat Activity yang sudah ada, remove Activity, edit Activity, melihat Activities page, melihat Activity dengan lebih rinci, melihat statistika dari data Activities 
- **Template:** HTML Menyediakan tempat untuk CRUD pada modul Activities, memfilter Activities, dan melihat statistik dari Activities.

---

### 5. 🎫 Ticket — _Syakirah_
Modul Tiket adalah sebuah sistem terintegrasi yang dirancang untuk menyederhanakan proses pemesanan tiket masuk ke berbagai fasilitas olahraga. Modul ini menjembatani kebutuhan pengguna untuk mendapatkan akses yang mudah dan cepat, dengan kebutuhan administrator fasilitas untuk mengelola pesanan secara efisien dan terorganisir.
Fungsionalitas modul ini sebagai berikut:
- **User:** dapat dengan mudah mencari fasilitas olahraga yang diinginkan, memeriksa ketersediaan jadwal secara real-time, dan melakukan pemesanan tiket untuk tanggal serta waktu spesifik.
- **Administrator:** dapat memantau semua transaksi secara real-time melalui dashboard, melihat detail setiap pemesanan, dan melacak pendapatan dengan mudah.

**Implementasi MVT Django:**
- **Model:** Menyimpan data pemesan dan data-data lain seperti nama username yang memesan, tempat yang tiketnya dipesan, harga pemesanan, waktu pemesanan, waktu tiket masuk. 
- **View:** Menyediakan logic untuk memesan tiket masuk, menampilkan tiket yang sudah dipesan, edit pemesanan, dan hapus pemesanan.
- **Template:** Menyediakan interface untuk menampilkan daftar pemesanan, halaman detail.

---

### 6. 📍 Place — _Justin_
Modul Place memungkinkan pengguna untuk melihat berbagai rekomendasi tempat latihan yang tersedia. Fungsionalitas utamanya adalah:
Fungsionalitas:
- **User:** mencari tempat, melihat detail, memesan, memberi rating dan ulasan.  
- **Facility Administrator:** mendaftarkan fasilitas olahraganya, mengelola halaman informasi tempat dan memantau data pemesanan yang masuk.

**Implementasi MVT Django:**
- **Model:** Menyimpan data tempat (nama, lokasi, deskripsi).  
- **View:** Mengelola logika untuk menampilkan daftar dan detail tempat, memproses permintaan booking
- **Template:** Menyediakan interface untuk menampilkan daftar tempat, halaman detail.

---

## 🧑‍💻 **Role atau Peran Pengguna**

| Role | Deskripsi |
|------|------------|
| **User** | Membuat dan mengedit Profile, melihat dan berbagi informasi di Forum, memantau aktivitas di Activities, melihat dan membeli perlengkapan di Shop, membeli tiket masuk fasilitas olahraga di Ticket, melihat rekomendasi tempat di Place Recommendation.|
| **Admin** | Memantau dan mengelola seluruh aktivitas aplikasi, moderasi Forum, mengelola data profile, memastikan modul Shop, Ticket, dan Place Recommendation berjalan lancar. |
| **Seller** | Menjual perlengkapan olahraga melalui modul Shop, mengelola produk (menambah, mengedit, dan menghapus), melihat pesanan. |
| **Facility Administrator** | Menyediakan tiket masuk fasilitas olahraga, mengelola profile tempat, melihat daftar pembeli tiket, memasukkan tempat ke dalam Place Recommendation. |

---

## 🔗 **Tautan Penting**

📂 **Dataset:**  
[Google Drive Dataset](https://drive.google.com/drive/folders/1N8zSOGo4KKSOg_YYxX-ngqi-TUjhA1hB)

🌐 **Deployment (PWS):**  
[Link Deployment](https://muhammad-kaila-triathlon.pbp.cs.ui.ac.id/)

🎨 **Figma Design:**  
[Figma Canvas Design](https://www.figma.com/design/jaqK9yFhlyMr03exmJUfVW/Design-Triathlon?node-id=0-1&t=RjX83ibJqvmN9suQ-1)

---

<div align="center">

✨ _Where athletes connect, grow, and go further together._ 💪  
Proudly Present by **Team D1**

</div>
