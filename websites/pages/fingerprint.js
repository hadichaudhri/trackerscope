import FingerprintJS from "@fingerprintjs/fingerprintjs";
import { useEffect } from "react";

import { db } from "../db/firebase";
import { doc, setDoc } from "firebase/firestore";

export const getFingerprint = async () => {
    const fp = await FingerprintJS.load();
    const result = await fp.get();
    return result.visitorId; // This is the unique fingerprint for the visitor
};

export async function getServerSideProps({ req }) {
    const forwarded = req.headers["x-forwarded-for"];
    const ip = forwarded
        ? forwarded.split(/, /)[0]
        : req.connection.remoteAddress;
    return {
        props: {
            ip,
        },
    };
}

export default function Fingerprint({ ip }) {
    useEffect(() => {
        const fetchFingerprint = async () => {
            const fingerprint = await getFingerprint();
            console.log("Device Fingerprint:", fingerprint);

            const docRef = doc(db, "fingerprints", fingerprint);

            const userInfo = {
                timestmap: new Date(),
                userAgent: navigator.userAgent,
                os: navigator.platform,
                screenSize: `${window.screen.width}x${window.screen.height}`,
                hardware: navigator.hardwareConcurrency,
                deviceModel: navigator.deviceMemory,
                ip,
            };

            console.log("User Info:", userInfo);

            try {
                await setDoc(docRef, {
                    userInfo,
                });
                console.log("Document written with ID: ", docRef.id);
            } catch (error) {
                console.error("Error adding document: ", error);
            }
        };

        fetchFingerprint();
    }, []);

    return (
        <>
            <h1>Fingerprint</h1>
            <p>
                Fingerprint is a unique identifier generated by the web browser
                when a user visits a website. Fingerprinting is a technique used
                to track users across websites without using cookies
            </p>
        </>
    );
}
