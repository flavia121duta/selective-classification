import React, { useState, useEffect } from "react";
import upload_icon from "./assets/upload.png";

export default function App() {
    const [file, setFile] = useState<File | null>(null);
    const [fileName, setFileName] = useState("");
    const [progress, setProgress] = useState(0);
    const [loading, setLoading] = useState(false);
    const [downloadUrl, setDownloadUrl] = useState<string | null>(null);

    // SSE for progress
    useEffect(() => {
        const eventSource = new EventSource("http://localhost:8000/progress");
        eventSource.onmessage = (event) => {
            setProgress(Number(event.data));
        };
        return () => eventSource.close();
    }, []);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        const f = e.target.files?.[0];
        if (f) {
            setFile(f);
            setFileName(f.name);
            setDownloadUrl(null);
            setProgress(0);
        }
    };

    const uploadFile = async () => {
        if (!file) return;
        setLoading(true);

        const formData = new FormData();
        formData.append("file", file);

        try {
            const response = await fetch("http://localhost:8000/classify", {
                method: "POST",
                body: formData,
            });
            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            setDownloadUrl(url);
        } catch (error) {
            alert("Error processing file");
            console.error(error);
        }

        setLoading(false);
    };

    return (
        <div style={styles.container}>
            <h1>Cosmetic Product Classifier</h1>

            <label style={styles.button}>
                <img src={upload_icon} alt="upload icon" width={20} height={20} style={{ marginRight: 8 }} />
                Upload Excel
                <input type="file" accept=".xlsx" onChange={handleFileChange} style={{ display: "none" }} />
            </label>

            {fileName && <p>Selected file: <strong>{fileName}</strong></p>}

            <br />

            <button style={styles.submit} onClick={uploadFile} disabled={!file || loading}>
                {loading ? "Processing data, please wait..." : "Classify Products"}
            </button>

            {loading && (
                <div style={{ marginTop: 10 }}>
                    <p>Progress: {progress}%</p>
                    <div style={styles.progressBarOuter}>
                        <div style={{ ...styles.progressBarInner, width: `${progress}%` }}></div>
                    </div>
                </div>
            )}

            {downloadUrl && (
                <a href={downloadUrl} download="produse_clasificate.xlsx" style={styles.download}>
                    Download Selective
                </a>
            )}
        </div>
    );
}

const styles: { [key: string]: React.CSSProperties } = {
    container: {
        maxWidth: 500,
        margin: "40px auto",
        textAlign: "center",
        fontFamily: "Arial, sans-serif"
    },
    button: {
        marginTop: 15,
        padding: "10px 20px",
        cursor: "pointer", display:
            "inline-flex", alignItems:
            "center", border:
            "1px solid #ccc",
        borderRadius: 4,
        background: "#f4f4f4"
    },
    submit: {
        margin: 15,
        padding: "10px 20px",
        fontSize: 16,
        cursor: "pointer"
    },
    progressBarOuter: {
        width: "100%",
        height: 10,
        background:
            "#eee", borderRadius: 5
    },
    progressBarInner: {
        height: "100%",
        background: "#4caf50",
        borderRadius: 5
    },
    download: {
        display: "inline-block",
        marginTop: 20,
        padding: "10px 20px",
        background: "#4caf50",
        color: "black",
        textDecoration: "none",
        borderRadius: 4,
        border: "1px solid black",
    },
};