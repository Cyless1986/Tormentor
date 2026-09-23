package de.tormentor.app;

import java.io.*;

/** Mono 16 kHz PCM, streamed to disk; the header remains valid after every block. */
final class PcmWaveFile implements Closeable {
    private final RandomAccessFile output;
    private long size;
    private boolean closed;
    PcmWaveFile(File file) throws IOException {
        output=new RandomAccessFile(file,"rw");
        output.setLength(0);
        output.writeBytes("RIFF");writeInt(36);output.writeBytes("WAVEfmt ");writeInt(16);
        writeShort(1);writeShort(1);writeInt(16000);writeInt(32000);writeShort(2);writeShort(16);
        output.writeBytes("data");writeInt(0);
    }
    private void writeInt(long value)throws IOException{for(int i=0;i<4;i++)output.write((int)(value>>(8*i))&255);}
    private void writeShort(int value)throws IOException{output.write(value&255);output.write((value>>8)&255);}
    synchronized void write(byte[] bytes,int count)throws IOException{
        if(closed)throw new IOException("Aufnahme bereits beendet.");
        if(count<0||count>bytes.length||count%2!=0)throw new IOException("Ungültige Audiodaten.");
        if(size+count>1024L*1024*1024-44)throw new IOException("Aufnahme erreicht 1 GB. Bitte eine neue Sitzung starten.");
        output.seek(44+size);output.write(bytes,0,count);size+=count;
        output.seek(4);writeInt(36+size);output.seek(40);writeInt(size);
    }
    public synchronized void close()throws IOException{if(!closed){closed=true;output.close();}}
}
