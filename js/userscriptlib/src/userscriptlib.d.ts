export {};
declare global {
    interface Navigator {
        msSaveOrOpenBlob: any;
    }
    var GM_xmlhttpRequest: any;
    function addButton(name: string, onclick: () => void, hotkey?: string): void;
    function addText(text: string, { color }: {
        color?: string;
    }): void;
    function findElementByXPath(exp: string): Node;
    function findElementByText(text: string): Node;
    function waitForSelector(selector: string): Promise<unknown>;
    function waitForText(text: string): Promise<unknown>;
    function waitForXPath(xpath: string): Promise<unknown>;
    function saveAsFile(data: string, filename: string, type: string): void;
    function download(url: string, filename?: string): void;
    function exec(args: string, callback?: (result: string) => void): void;
    function openInNewWindow(url: string): void;
}
