#include <stdio.h>
#include <string.h>
#include <winsock2.h>
#include <windows.h>
#include <stdint.h>
#include <vector>
#include <iostream>
#include <sstream>


#pragma comment(lib, "ws2_32.lib")

// Base64编码函数
std::string base64_encode(const unsigned char* data, size_t input_length) {
    static const char encode_table[] = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    std::string encoded;
    encoded.reserve(((input_length + 2) / 3) * 4);
    for (size_t i = 0; i < input_length; i += 3) {
        uint32_t triple = data[i] << 16;
        if (i + 1 < input_length) triple |= data[i + 1] << 8;
        if (i + 2 < input_length) triple |= data[i + 2];
        encoded.push_back(encode_table[(triple >> 18) & 0x3F]);
        encoded.push_back(encode_table[(triple >> 12) & 0x3F]);
        encoded.push_back((i + 1 < input_length) ? encode_table[(triple >> 6) & 0x3F] : '=');
        encoded.push_back((i + 2 < input_length) ? encode_table[triple & 0x3F] : '=');
    }
    return encoded;
}

// SHA1哈希函数
std::vector<uint8_t> sha1(const std::string& input) {
    std::vector<uint8_t> digest(20);
    HCRYPTPROV hProv = 0;
    HCRYPTHASH hHash = 0;

    if (CryptAcquireContext(&hProv, NULL, NULL, PROV_RSA_AES, CRYPT_VERIFYCONTEXT) &&
        CryptCreateHash(hProv, CALG_SHA1, 0, 0, &hHash)) {
        CryptHashData(hHash, (const BYTE*)input.c_str(), input.size(), 0);
        DWORD hash_len = 20;
        CryptGetHashParam(hHash, HP_HASHVAL, digest.data(), &hash_len, 0);
    }

    if (hHash) CryptDestroyHash(hHash);
    if (hProv) CryptReleaseContext(hProv, 0);

    return digest;
}

// WebSocket握手函数
std::string websocket_handshake(const std::string& request) {
    std::string key;
    const std::string magic_string = "258EAFA5-E914-47DA-95CA-C5AB0DC85B11";
    size_t key_start = request.find("Sec-WebSocket-Key: ") + 19;
    size_t key_end = request.find("\r\n", key_start);
    key = request.substr(key_start, key_end - key_start);
    key += magic_string;

    std::vector<uint8_t> sha1_result = sha1(key);
    std::string accept_key = base64_encode(sha1_result.data(), sha1_result.size());

    std::stringstream response;
    response << "HTTP/1.1 101 Switching Protocols\r\n"
        << "Upgrade: websocket\r\n"
        << "Connection: Upgrade\r\n"
        << "Sec-WebSocket-Accept: " << accept_key << "\r\n\r\n";
    return response.str();
}

// 处理WebSocket帧
void handle_websocket_frame(SOCKET client_socket, const std::vector<uint8_t>& frame) {
    // 解码有效载荷
    size_t payload_length = frame[1] & 0x7F;
    size_t masking_key_start = 2;
    if (payload_length == 126) masking_key_start = 4;
    if (payload_length == 127) masking_key_start = 10;
    size_t payload_start = masking_key_start + 4;

    std::vector<uint8_t> decoded_payload(payload_length);
    for (size_t i = 0; i < payload_length; ++i) {
        decoded_payload[i] = frame[payload_start + i] ^ frame[masking_key_start + (i % 4)];
    }

    std::string received_message(decoded_payload.begin(), decoded_payload.end());
    printf("Received from client: %s\n", received_message.c_str());

    // 准备响应帧
    std::string response_message = "Server Response: " + received_message;
    std::vector<uint8_t> response_frame;
    response_frame.push_back(0x81); // 文本帧，FIN=1
    response_frame.push_back(response_message.size()); // 无掩码，长度
    response_frame.insert(response_frame.end(), response_message.begin(), response_message.end());

    // 发送响应数据
    send(client_socket, (const char*)response_frame.data(), response_frame.size(), 0);
}

int kain() {
    // 初始化WSA
    WSADATA wsaData;
    WSAStartup(MAKEWORD(2, 2), &wsaData);

    SOCKET server_socket = socket(AF_INET, SOCK_STREAM, IPPROTO_TCP);

    sockaddr_in server_addr;
    server_addr.sin_family = AF_INET;
    server_addr.sin_port = htons(8888);
    server_addr.sin_addr.s_addr = inet_addr("127.0.0.1");

    bind(server_socket, (sockaddr*)&server_addr, sizeof(server_addr));
    listen(server_socket, 5);

    printf("Server is listening on port 8888...\n");

    SOCKET client_socket;
    sockaddr_in client_addr;
    int client_addr_len = sizeof(client_addr);
    char buffer[1024];

    while (true) {
        client_socket = accept(server_socket, (sockaddr*)&client_addr, &client_addr_len);
        if (client_socket == INVALID_SOCKET) {
            printf("accept error!\n");
            continue;
        }

        // 输出客户端IP地址和端口
        printf("Connection established with IP: %s, Port: %d\n",
            inet_ntoa(client_addr.sin_addr),
            ntohs(client_addr.sin_port));

        int recv_len = recv(client_socket, buffer, 1024, 0);
        if (recv_len > 0) {
            std::string request(buffer, recv_len);
            std::string response = websocket_handshake(request);
            send(client_socket, response.c_str(), response.size(), 0);
        } 

        while (true) {
            recv_len = recv(client_socket, buffer, 1024, 0);
            if (recv_len <= 0) break;

            std::vector<uint8_t> frame(buffer, buffer + recv_len);
            handle_websocket_frame(client_socket, frame);
        }

        printf("Connection closed by client.\n");
        closesocket(client_socket);
    }

    closesocket(server_socket);
    WSACleanup();
    return 0;
}

