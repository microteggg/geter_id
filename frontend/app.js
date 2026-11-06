/*
 * Untuk lokal:
 * http://127.0.0.1:8000
 *
 * Ketika backend sudah dideploy,
 * URL ini akan kita ganti dengan URL production.
 */
const API_BASE_URL =
    "http://127.0.0.1:8000";


const apiStatus =
    document.getElementById("apiStatus");

const symbolInput =
    document.getElementById("symbolInput");

const searchButton =
    document.getElementById("searchButton");

const message =
    document.getElementById("message");

const stockResult =
    document.getElementById("stockResult");

const stockSymbol =
    document.getElementById("stockSymbol");

const stockData =
    document.getElementById("stockData");


async function checkAPI() {

    try {

        const response = await fetch(
            `${API_BASE_URL}/api/health`,
            {
                cache: "no-store"
            }
        );

        if (!response.ok) {
            throw new Error(
                `HTTP ${response.status}`
            );
        }

        const data =
            await response.json();

        if (data.status !== "ok") {
            throw new Error(
                "API belum siap"
            );
        }

        apiStatus.textContent =
            "API Online";

        apiStatus.className =
            "status online";

    } catch (error) {

        apiStatus.textContent =
            "API Offline";

        apiStatus.className =
            "status offline";

    }

}


async function searchStock() {

    const symbol =
        symbolInput.value
            .trim()
            .toUpperCase();

    if (!symbol) {

        showMessage(
            "Masukkan kode saham terlebih dahulu.",
            true
        );

        return;
    }


    searchButton.disabled =
        true;

    searchButton.textContent =
        "Loading...";

    stockResult.classList.add(
        "hidden"
    );

    showMessage(
        `Mengambil data ${symbol}...`
    );


    try {

        const response = await fetch(
            `${API_BASE_URL}/api/quote/${encodeURIComponent(symbol)}`,
            {
                cache: "no-store"
            }
        );


        const payload =
            await response.json();


        if (!response.ok) {

            const detail =
                payload.detail ||
                "Gagal mengambil data saham.";

            throw new Error(detail);

        }


        stockSymbol.textContent =
            payload.symbol;

        stockData.textContent =
            JSON.stringify(
                payload.data,
                null,
                2
            );


        stockResult.classList.remove(
            "hidden"
        );

        showMessage(
            `Data ${symbol} berhasil diterima dari backend.`
        );


    } catch (error) {

        showMessage(
            error.message,
            true
        );

    } finally {

        searchButton.disabled =
            false;

        searchButton.textContent =
            "Analisis";

    }

}


function showMessage(
    text,
    isError = false
) {

    message.textContent =
        text;

    message.className =
        isError
            ? "message error"
            : "message";

}


searchButton.addEventListener(
    "click",
    searchStock
);


symbolInput.addEventListener(
    "keydown",
    (event) => {

        if (event.key === "Enter") {
            searchStock();
        }

    }
);


checkAPI();
