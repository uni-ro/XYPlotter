#include <iostream>
#include <string>
#include <algorithm>
#include <iostream>
#include <fstream>
#include <sstream>
#include <cmath>
#include <cstdint>
#include <typeinfo>

using namespace std;

int64_t strToInt(string inputString);

struct Point
{
    double xPos;
    double yPos;
};


int main(int argc, char* argv[])
{
    ifstream dataFile;
    int64_t dataContents;
    int8_t divisor;
    //uint64_t divisor = strToInt(argv[1]);

    Point point;

    dataFile.open("test.bin", ios::binary | ios::in);

    double testDouble = 123456789.123456789;

    if(!dataFile.is_open())
    {
        return 0;
    }

    int i = 0;

    while(i < strToInt(argv[1]))
    {

        dataFile.read((char *) &dataContents, 8);
        dataFile.read((char *) &divisor, 1);

        cout << dataContents << "\n";
        
        double * currPoint = (i % 2 == 0) ? &point.xPos : &point.yPos;

        *currPoint = (double) dataContents * pow(10, divisor); //((double) dataContents) / ((double) divisor);

        cout << "The value is: " << *currPoint << "\n";
        
        i++;
    }
    

    dataFile.close();

    return 1;
}

int64_t strToInt(string inputStr)
{
    
    int64_t strVal = 0;

    for (int i = 0; i < inputStr.length(); i++)
    {
        char currentChar = inputStr[i];

        int currInt = ((int) currentChar) - 48;

        strVal += currInt * pow(10, inputStr.length() - 1 - i);
    }

    return strVal;
}