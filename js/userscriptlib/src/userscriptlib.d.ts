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
    function findElementBySelector(selector: string): Node | null;
    function findElementByXPath(exp: string): Node | null;
    function findElementByText(text: string): Node | null;
    function waitForSelector(selector: string): Promise<Node | null>;
    function waitForText(text: string): Promise<Node | null>;
    function waitForXPath(xpath: string): Promise<Node | null>;
    function saveAsFile(data: string, filename: string, type: string): void;
    function download(url: string, filename?: string): void;
    function exec(args: string | string[]): Promise<string>;
    function openInNewWindow(url: string): void;
    function getSelectedText(): void;
    function sendText(text: string): void;
    function click(el: HTMLElement): void;
}
