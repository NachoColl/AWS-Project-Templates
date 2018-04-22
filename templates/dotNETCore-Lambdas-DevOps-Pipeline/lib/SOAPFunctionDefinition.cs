using System;
using System.Collections.Generic;
using System.IO;
using System.Xml;

namespace nWAY.Library.SOAP {
    public class SOAPFunctionDefinition {

        public string FunctionName {get;set;}
        public List<string> FunctionAttributes { get;set;}
    
        public static SOAPFunctionDefinition ParseXMLEnvelopeCall(string Body){
            
            SOAPFunctionDefinition result = new SOAPFunctionDefinition();
            result.FunctionAttributes = new List<string>();

            bool startPointDetected = false; bool functionNameDetected=false;
            using (XmlTextReader xmlReader = new XmlTextReader(new StringReader(Body)))
            {
                while (xmlReader.Read())
                {
                    if (xmlReader.IsStartElement())
                    {
                        if (startPointDetected && !functionNameDetected){
                            result.FunctionName = xmlReader.Name;
                            functionNameDetected = true;
                        }else if (startPointDetected && functionNameDetected) {
                            result.FunctionAttributes.Add(xmlReader.ReadElementContentAsString());
                        }else if (xmlReader.Name == "soap:Body")
                            startPointDetected = true;              
                    }                
                }
            }
            return result;
        } 

         public static string CreateSOAPResponse(string FunctionName, string FunctionResult){        
            return String.Format("<?xml version=\"1.0\" encoding=\"utf-8\"?><soap:Envelope xmlns:soap=\"http://schemas.xmlsoap.org/soap/envelope/\" xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xmlns:xsd=\"http://www.w3.org/2001/XMLSchema\"><soap:Body><{0}Response xmlns=\"http://api.mapme.net/\"><{0}Result>{1}</{0}Result></{0}Response></soap:Body></soap:Envelope>", FunctionName, FunctionResult);
        } 
    }


}

