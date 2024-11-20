import FingerprintJS from "@fingerprintjs/fingerprintjs";

export const getFingerprint = async () => {
    const fp = await FingerprintJS.load();
    const result = await fp.get();
    return result.visitorId; // This is the unique fingerprint for the visitor
};
