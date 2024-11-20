import { useEffect, useState } from "react";
import { getFingerprint } from "../utils/fingerprint";
import { db } from "../db/firebase";
import { doc, getDoc } from "firebase/firestore";

export default function Tracked({ cookie }) {
    // // Store a cookie on the user's computer
    // const cookieStore = await cookies();
    // const cookie = cookieStore.set("userID", "1234");
    const [localStorageFound, setLocalStorageFound] = useState("False");
    const [fingerprint, setFingerprint] = useState();
    const [whoisData, setWhoisData] = useState();

    useEffect(() => {
        if (localStorage.getItem("userID")) {
            setLocalStorageFound("True");
        }

        checkFindgerprint();
    });

    async function checkFindgerprint() {
        const fingerprint = await getFingerprint();
        console.log("Device Fingerprint:", fingerprint);
        const docRef = doc(db, "fingerprints", fingerprint);
        const docSnap = await getDoc(docRef);
        if (docSnap.exists() && whoisData === undefined) {
            console.log("Document data:", docSnap.data());

            // Convert the data to a string
            const data = JSON.stringify(docSnap.data());
            console.log("Document data as a string:", data);
            setFingerprint(data);

            // Get the IP address from the document
            const ip = docSnap.data().userInfo.ip;
            console.log("IP Address:", ip);

            // Get the WHOIS data for the IP address from the API
            const response = await fetch(`/api/whois?ip=${ip}`);
            console.log("WHOIS response:", response);
            const whois = await response.json();
            console.log("WHOIS data:", whois);

            // Construct a div for each key-value pair in the WHOIS data
            const divs = Object.entries(whois).map(([key, value]) => (
                <div key={key}>
                    <strong>{key}:</strong> {value}
                </div>
            ));
            setWhoisData(divs);
        } else {
            console.log("No such document!");
        }
    }

    return (
        <>
            <h1>Am I being tracked?</h1>
            <br></br>
            <div>Cookies found: {cookie}</div>
            <br></br>
            <div>Local storage found: {localStorageFound}</div>
            <br></br>
            <div>Decide fingerprint found: {fingerprint}</div>
            <br></br>
            <div>WHOIS data: {whoisData}</div>
        </>
    );
}

export const getServerSideProps = async (context) => {
    // If we've seen this person before, display a "Welcome back!" message
    const tracking = context.req.cookies.tracking;
    if (tracking === "true") {
        return { props: { cookie: "True" } };
    }

    return { props: { cookie: "False" } };
};
