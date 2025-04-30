# Image Signing & Steganographic Signature Embedding

## Overview

This project provides a complete pipeline to digitally sign PNG images with a 4096-bit RSA keypair, embed the signature stealthily inside the image file, verify authenticity, and demonstrate tamper detection. By hiding the signature across standard PNG metadata fields (and compressing it to look like random data), the solution:

- **Protects integrity**: any change—even a single bit—will break the signature.  
- **Maintains usability**: signed images open and display normally in any viewer.  
- **Enhances stealth**: signature data is split, compressed, and tucked into innocuous fields.

### Potential Applications

- **Secure Content Distribution**  
  Photographers, designers, or agencies can distribute signed imagery. Recipients verify authenticity without specialized tools.  
- **Copyright & Ownership Proof**  
  Embedding a hidden signature provides cryptographic proof of authorship and prevents undetected unauthorized modifications.  
- **Document & Evidence Integrity**  
  In legal, medical, or archival contexts, images (e.g., scans, X-rays, blueprints) can be signed to guarantee they remain unaltered.  
- **Anti-counterfeiting in Manufacturing**  
  Digital labels or product photos can carry hidden, verifiable signatures to prove genuine origin.  

---

## Detailed Approach

### 1. Key Generation

- **RSA-4096** is chosen for strong security and widespread support.  
- Use OpenSSL locally:
  ```bash
  openssl genpkey -algorithm RSA -pkeyopt rsa_keygen_bits:4096 -out private.pem
  openssl rsa -in private.pem -pubout -out public.pem

### 2. Signing & Embedding

#### Normalize Image
Load the PNG and convert it to **RGBA** mode so the underlying byte sequence is deterministic.

#### Generate Signature
Compute the RSA signature over the raw image bytes:

```text
signature = RSA_sign(private_key, image_bytes, SHA256)
```

#### Compress & Encode
* Compress the binary signature with **zlib**.
* Base64‑encode the compressed bytes.

> The result looks like random text, making the signature hard to notice.

#### Split for Stealth
Divide the encoded signature evenly into **two halves**.

#### Embed in PNG Metadata
Use three standard *tEXt* chunks:

| Field       | Purpose                              |
|-------------|--------------------------------------|
| `Software`  | e.g. `MyImageSigner v1.0` (benign)   |
| `Comment`   | **1st half** of the signature        |
| `Description` | **2nd half** of the signature       |

Save the result as **`signed.png`**. Ordinary image viewers ignore unknown or extra text chunks, so the picture looks untouched.

---

### 3. Verification

#### Load Public Key
Have the signer’s corresponding **public key** ready.

#### Open & Normalize
Read the target PNG in RGBA mode to reproduce *exactly* the byte sequence that was signed.

#### Extract & Reassemble
1. Read the `Comment` and `Description` chunks.
2. Concatenate the halves.
3. Base64‑decode, then zlib‑decompress to recover the raw signature.

#### Verify
Run the RSA check:

```text
RSA_verify(public_key, image_bytes, signature, SHA256)
```

* ✔️ **Signature valid** – image is authentic.
* ❌ **Invalid or tampered** – image data or metadata has changed.

---

### 4. Tamper Demonstration
**Goal:** Prove that even a 1‑bit change is detected.

1. Open `signed.png` (keep all metadata).
2. Flip the least‑significant bit (LSB) of the red channel at pixel **(0, 0)**.
3. Save as `signed_tampered.png` with the original text chunks intact.
4. Run verification – it should fail, showing that any alteration is caught.

---

## Conclusion & Future Enhancements
This method delivers a clean, modular, and stealthy approach to image signing with robust tamper detection.

#### Possible Extensions
* **LSB steganography** – embed the signature bits directly into pixel data.
* **Chunk obfuscation** – use randomized or non‑standard chunk names to hide the signature.
* **JPEG/EXIF support** – adapt the concept to JPEG by storing the signature in EXIF tags.
* **Key‑management integration** – automate secure key storage and rotation.

By following this design, you ensure cryptographic integrity for images in any application where authenticity and undetectable tampering are critical.





